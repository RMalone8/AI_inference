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
        for variant_key, variant_data in model_data['variants'].items():
            if runtime in variant_data:
                model_name = variant_data[runtime]['name']
                display_name = variant_data['display_name']
                model_pairs.append([model_name, display_name])
    
    return model_pairs

def render_templates(machine, runtime):
    config_dir = f"{os.path.dirname(os.path.abspath(__file__))}/remote_config"
    env = Environment(loader=FileSystemLoader(config_dir))
    
    template_compose = env.get_template("remote_compose.j2")
    template_prom = env.get_template("remote_prom_config.j2")
    
    rendered_compose = template_compose.render({"machine": machine, "runtime": runtime})
    rendered_prom = template_prom.render({
        "machine": machine, 
        "runtime": runtime,
    })
    
    with open("remote_config/remote_compose.yaml", "w") as f:
        f.write(rendered_compose)
    with open("remote_config/remote_prom_config.yml", "w") as f:
        f.write(rendered_prom)

@click.command()
@click.option('--machine', help='The machine to deploy the models onto', default="jetson")
@click.option('--runtime', help='The runtime to serve the models on', default="vllm")
@click.option('--model', help='What aspect of the stack is varied', default="granite")
def main(machine, runtime, model):

    if runtime != "variable":
        model_pairs = load_models(runtime)

    for i in range(2): # just picking 2 for now
        if model == "variable":
            config = get_machine_config(machine, runtime)
            setup_environment(machine, model_pairs[i])
        elif runtime == "variable":
            rt = "vllm" if i == 0 else "ollama"
            model_pairs = load_models(rt)
            config = get_machine_config(machine, rt)
            setup_environment(machine, model_pairs[0])
        elif machine == "variable":
            m = "jetson" if i == 0 else "armchair"
            config = get_machine_config(m, runtime)
            setup_environment(machine, model_pairs[0])
    
        os.environ["SERVER_IMAGE"] = config.get("server_image", "")
        os.environ["SERV_VOL"] = config.get("server_vol", "")
        os.environ["HOST_SOCK"] = config.get("host_sock", "")

        if model == "variable":
            render_templates(machine, runtime)
        if runtime == "variable":
            render_templates(machine, rt)
        if machine == "variable":
            render_templates(m, runtime)

        run(config["command"])


if __name__ == '__main__':
    main()