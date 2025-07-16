import click
from invoke import run
from jinja2 import Environment, FileSystemLoader
import os
import yaml
import json
from datetime import datetime
from prometheus_api_client import PrometheusConnect

def get_machine_config(machine, runtime):
    configs = {
        "armchair": {
            "ollama": {
                "server_image": "docker.io/ollama/ollama:latest",
                "server_vol": "ollama_models:/root/.ollama",
                "host_sock": "/run/user/1001/podman/podman.sock",
                "command": "sh startup.sh"
            },
            "vllm": {
                "server_image": "public.ecr.aws/q9t5s3a7/vllm-cpu-release-repo:v0.9.1",
                "server_vol": "vllm_cache:/root/.cache/huggingface",
                "host_sock": "/run/user/1001/podman/podman.sock",
                "command": "sh startup.sh"
            }
        },
        "jetson": {
            "ollama": {
                "server_image": "docker.io/dustynv/ollama:0.6.8-r36.4-cu126-22.04",
                "server_vol": "ollama:/data/models/ollama",
                "host_sock": "/run/podman/podman.sock",
                "command": "python jetson.py"
            },
            "vllm": {
                "server_image": "docker.io/dustynv/vllm:0.8.6-r36.4-cu128-24.04",
                "server_vol": "vllm_cache:/root/.cache/huggingface",
                "host_sock": "/run/podman/podman.sock",
                "command": "python jetson.py"
            }
        }
    }
    
    if machine in configs and runtime in configs[machine]:
        return configs[machine][runtime]
    return {"command": f"echo 'Invalid machine: {machine} or runtime: {runtime}'"}

def setup_environment(config, iter_no):
    if config['machine'] == "armchair":
        os.environ["CONTAINER_HOST"] = "ssh://ryan@ewr0.nichi.link:9022/run/user/1001/podman/podman.sock"
        os.environ["CONTAINER_SSHKEY"] = "/Users/rmalone/.ssh/id_ed25519"
    
    os.environ["ITER_NO"] = str(iter_no)
    os.environ["MODEL_PATH"] = config['model_path']
    os.environ["MODEL_NAME"] = config['model_name']
    os.environ["WEBUI"] = str(config['webui'])
    os.environ["SERVER_PORT"] = "8000" if config['runtime'] == "vllm" else "11434"

    if "HF_TOKEN" in os.environ:
        os.environ["HF_TOKEN"] = os.environ["HF_TOKEN"]

def load_stack_configs(config_args: dict):
    
    configs = []
    stack_count = 0

    # if a config path is provided, load the configs from the file
    stacks_file = f"{os.path.dirname(os.path.abspath(__file__))}/{config_args['config_path']}"
    with open(stacks_file, 'r') as f:
        stacks_yaml = yaml.safe_load(f)

    for stack_name, stack_data in stacks_yaml['stacks'].items():

        config = {
            "name": stack_name,
            "machine": stack_data['machine'],
            "runtime": stack_data['runtime'],
            "model_name": stack_data['model_name'],
            "model_path": stack_data['model_path'],
            "temp": stack_data.get('temp', 0.0),
            "context": stack_data.get('context', None),
            "gpu": stack_data.get('gpu', True),
            "webui": stack_data.get('webui', False),
        }

        if config['webui'] and config['runtime'] == "ollama":
            config["model_name"] = "test"
            config["model_path"] = "test"

        configs.append(config)
        stack_count += 1
    
    return configs, stack_count

def render_templates(config):
    remote_config_dir = f"{os.path.dirname(os.path.abspath(__file__))}/remote_config"
    local_config_dir = f"{os.path.dirname(os.path.abspath(__file__))}/local_config"

    remote_env = Environment(loader=FileSystemLoader(remote_config_dir))
    local_env = Environment(loader=FileSystemLoader(local_config_dir))

    
    template_remote_compose = remote_env.get_template("remote_compose.j2")
    template_remote_prom = remote_env.get_template("remote_prom_config.j2")
    template_local_compose = local_env.get_template("local_compose.j2")
    
    rendered_remote_compose = template_remote_compose.render(config)
    rendered_remote_prom = template_remote_prom.render(config)
    rendered_local_compose = template_local_compose.render(config)

    with open(f"{remote_config_dir}/remote_compose.yaml", "w") as f:
        f.write(rendered_remote_compose)
    with open(f"{remote_config_dir}/remote_prom_config.yml", "w") as f:
        f.write(rendered_remote_prom)
    with open(f"{local_config_dir}/local_compose.yaml", "w") as f:
        f.write(rendered_local_compose)

def store_results(config, iter_no):

    prometheus_url = "http://localhost:9090"
    prometheus_client = PrometheusConnect(url=prometheus_url)

    power_stddev_query = f'''stddev_over_time(
    (
        consumed_power{{statistic="power"}}
        * on() group_left(model_specs)
        (
            client_running_{config['model_name']}_{iter_no} == 1
        )
    )[1h:5s]
    )'''
    gpu_memory_query = "gpu_mem_used * 1024 * 1024"
    power_consumption_query = f'''avg_over_time(
    (
        consumed_power{{statistic="power"}}
        * on() group_left(model_specs)
        (
            client_running_{config['model_name']}_{iter_no} == 1
        )
    )[1h:5s]
    )'''
    avg_time_per_iter_query = f'last_over_time(client_avg_time_per_iter_{config['model_name']}_{iter_no}[10m])'
    token_per_sec_per_iter_query = f'last_over_time(client_avg_token_per_sec_per_iter_{config['model_name']}_{iter_no}[10m])'

    power_stddev_result = prometheus_client.custom_query(power_stddev_query)
    gpu_memory_result = prometheus_client.custom_query(gpu_memory_query)
    power_consumption_result = prometheus_client.custom_query(power_consumption_query)
    avg_time_per_iter_result = prometheus_client.custom_query(avg_time_per_iter_query)
    token_per_sec_per_iter_result = prometheus_client.custom_query(token_per_sec_per_iter_query)

    print(power_stddev_result)
    print(gpu_memory_result)
    print(power_consumption_result)
    print(avg_time_per_iter_result)
    print(token_per_sec_per_iter_result)

    results_file = f"{os.path.dirname(os.path.abspath(__file__))}/results/results.json"
    with open(results_file, "r") as f:
        results = json.load(f)

    config['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    config['data'] = {
        "power_stddev": power_stddev_result,
        "gpu_memory": gpu_memory_result,
        "power_consumption": power_consumption_result,
        "avg_time_per_iter": avg_time_per_iter_result,
        "token_per_sec_per_iter": token_per_sec_per_iter_result
    }

    for key, value in config['data'].items():
        for i in range(len(value)):
            new_val = float(value[i]['value'][1])
            if new_val > results['max_values'][key]:
                results['max_values'][key] = new_val
            if new_val < results['min_values'][key]:
                results['min_values'][key] = new_val

    results['stacks'][config['name']] = config

    with open(results_file, "w") as f:
        json.dump(results, f, indent=4)

@click.command()
@click.option('--powercycle', help='Whether to powercycle the machine', default=False)
@click.option('--config_path', help='The path to the config file', default="run_config.yaml")

def main(powercycle, config_path):
    
    config_args = {
        "powercycle": powercycle,
        "config_path": config_path
    }

    os.environ["POWERCYCLE"] = str(powercycle)

    template_configs, stack_count = load_stack_configs(config_args)

    for i in range(stack_count):
        config = get_machine_config(template_configs[i]['machine'], template_configs[i]['runtime'])
        os.environ["SERVER_IMAGE"] = config.get("server_image", "")
        os.environ["SERV_VOL"] = config.get("server_vol", "")
        os.environ["HOST_SOCK"] = config.get("host_sock", "")

        setup_environment(template_configs[i], i)
        render_templates(template_configs[i])

        run(config["command"])
        store_results(template_configs[i], i)
        os.environ["POWERCYCLE"] = "False" # we only need to powercycle once

if __name__ == '__main__':
    main()