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

def setup_environment(machine, model_pair):
    if machine == "armchair":
        os.environ["CONTAINER_HOST"] = "ssh://ryan@ewr0.nichi.link:9022/run/user/1001/podman/podman.sock"
        os.environ["CONTAINER_SSHKEY"] = "/Users/rmalone/.ssh/id_ed25519"
    
    os.environ["MODEL_NAME"] = model_pair[0]
    os.environ["MODEL_SPECS"] = model_pair[1]

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
                    model_name = variant_data[runtime]['name']
                    display_name = variant_data['display_name']
                    model_pairs.append([model_name, display_name])
        
    return model_pairs

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
def main(machine, runtime, model, temp, context, webui, gpu):

    template_config = {
        "machine": machine,
        "runtime": runtime,
        "model": model,
        "temp": 0.0,
        "context": 4096,
        "webui": webui,
        "gpu": True
    }

    model_index = 0

    for i in range(2): # just picking 2 for now

        if runtime != "variable":
            rt = runtime
        else:
            rt = "vllm" if i == 0 else "ollama"
            template_config["runtime"] = rt

        if model == "variable" or webui == "webui" and runtime == "vllm":
            model_index = i

        if machine == "variable":
            m = "jetson" if i == 0 else "armchair"
            template_config["machine"] = m
        else:
            m = machine

        if context == "variable":
            template_config["context"] = 4096 if i == 0 else 8192

        if temp == "variable":
            template_config["temp"] = 0.0 if i == 0 else 1.0

        if gpu == "variable":
            template_config["gpu"] = True if i == 0 else False

        model_pairs = load_models(rt)
        config = get_machine_config(m, rt)
        os.environ["SERVER_IMAGE"] = config.get("server_image", "")
        os.environ["SERV_VOL"] = config.get("server_vol", "")
        os.environ["HOST_SOCK"] = config.get("host_sock", "")
        if webui == "webui" and runtime == "ollama":
            setup_environment(m, ["test", "test"])
            template_config["model_specs"] = "test"
        else:
            setup_environment(m, model_pairs[model_index])
            template_config["model_specs"] = model_pairs[model_index][1]
        render_templates(template_config)

        run(config["command"])

if __name__ == '__main__':
    main()