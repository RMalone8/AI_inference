import click
from invoke import run
from jinja2 import Environment, FileSystemLoader
import os
import yaml

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

def setup_environment(config):
    if config['machine'] == "armchair":
        os.environ["CONTAINER_HOST"] = "ssh://ryan@ewr0.nichi.link:9022/run/user/1001/podman/podman.sock"
        os.environ["CONTAINER_SSHKEY"] = "/Users/rmalone/.ssh/id_ed25519"
    
    os.environ["MODEL_PATH"] = config['model_path']
    os.environ["MODEL_NAME"] = config['model_name']
    os.environ["WEBUI"] = str(config['webui'])
    os.environ["SERVER_PORT"] = "8000" if config['runtime'] == "vllm" else "11434"

    if "HF_TOKEN" in os.environ:
        os.environ["HF_TOKEN"] = os.environ["HF_TOKEN"]

def load_models(runtime):
    
    models_file = f"{os.path.dirname(os.path.abspath(__file__))}/models.yaml"
    with open(models_file, 'r') as f:
        models_config = yaml.safe_load(f)
    
    model_pairs = []
    for model_key, model_data in models_config['models'].items():
        if runtime == "ollama" and model_key == "gemma3" or runtime == "vllm" and model_key == "granite3":
        # right now, granite3 will only work on vllm because they can be downloaded at runtime and
        # ollama only supports gemma3 which is already downloaded
            for variant_key, variant_data in model_data['variants'].items():
                if runtime in variant_data:
                    model_path = variant_data[runtime]['name']
                    display_name = variant_data['display_name']
                    model_pairs.append([model_path, display_name])
        
    return model_pairs

def load_stack_configs(config_args: dict):
    
    configs = []
    stack_count = 0

    # if a config path is provided, load the configs from the file
    if config_args['config_path']:
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
    else: # otherwise, use the provided config args
        stack_count = 2 # just picking 2 for now
        for i in range(stack_count):
            config = {}

            model_index = 0

            if config_args['runtime'] == "variable":
                config["runtime"] = "vllm" if i == 0 else "ollama"
            else:
                config["runtime"] = config_args['runtime']

            if config_args['model'] == "variable" or config_args['webui'] == True and config_args['runtime'] == "vllm":
                model_index = i

            if config_args["machine"] == "variable":
                config["machine"] = "jetson" if i == 0 else "armchair"
            else:
                config["machine"] = config_args['machine']

            if config_args['context'] == "variable":
                config["context"] = 4096 if i == 0 else 8192
            elif config_args['context']:
                config["context"] = config_args['context']
            else:
                config["context"] = None

            if config_args['temp'] == "variable":
                config["temp"] = 0.0 if i == 0 else 1.0
            elif config_args['temp']:
                config["temp"] = config_args['temp']
            else:
                config["temp"] = 0.0

            if config_args['gpu'] == "variable":
                config["gpu"] = True if i == 0 else False
            else:
                config["gpu"] = config_args['gpu']

            config["webui"] = config_args['webui']

            model_pairs = load_models(config_args['runtime'])

            if config_args['webui'] == True and config_args['runtime'] == "ollama":
                config["model_name"] = "test"
                config["model_path"] = "test"
            else:
                config["model_name"] = model_pairs[model_index][1]  
                config["model_path"] = model_pairs[model_index][0]

            config["name"] = f"{config['machine']}-{config['runtime']}-{config['model_name']}-{i}"

        configs.append(config)
    
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

@click.command()
@click.option('--machine', help='The machine to deploy the models onto', default="jetson")
@click.option('--runtime', help='The runtime to serve the models on', default="ollama")
@click.option('--model', help='What aspect of the stack is varied', default="granite")
@click.option('--temp', help='The randomness of the model', default=None)
@click.option('--context', help='Extra aspects to control for', default=None)
@click.option('--webui', help='Whether to run the webui', default=False)
@click.option('--gpu', help='Whether to use the gpu', default=True)
@click.option('--powercycle', help='Whether to powercycle the machine', default=False)
@click.option('--config_path', help='The path to the config file', default=None)

def main(machine, runtime, model, temp, context, webui, gpu, powercycle, config_path):
    
    config_args = {
        "machine": machine,
        "runtime": runtime,
        "model": model,
        "temp": temp,
        "context": context,
        "webui": webui,
        "gpu": gpu,
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

        model_pair = [template_configs[i]['model_path'], template_configs[i]['model_name']]

        setup_environment(template_configs[i])
        render_templates(template_configs[i])

        run(config["command"])
        os.environ["POWERCYCLE"] = "False" # we only need to powercycle once

if __name__ == '__main__':
    main()