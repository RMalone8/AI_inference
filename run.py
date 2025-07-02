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

def render_templates(machine, runtime, model_specs, gpu=True, webui=False):
    remote_config_dir = f"{os.path.dirname(os.path.abspath(__file__))}/remote_config"
    local_config_dir = f"{os.path.dirname(os.path.abspath(__file__))}/local_config"

    remote_env = Environment(loader=FileSystemLoader(remote_config_dir))
    local_env = Environment(loader=FileSystemLoader(local_config_dir))

    
    template_remote_compose = remote_env.get_template("remote_compose.j2")
    template_remote_prom = remote_env.get_template("remote_prom_config.j2")
    template_local_compose = local_env.get_template("local_compose.j2")
    
    rendered_remote_compose = template_remote_compose.render({"machine": machine, "runtime": runtime, "gpu": gpu, "webui": webui})
    rendered_remote_prom = template_remote_prom.render({"machine": machine, "runtime": runtime, "model_specs": model_specs})
    rendered_local_compose = template_local_compose.render({"runtime": runtime, "webui": webui})

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
@click.option('--extra_args', help='Extra aspects to control for', default=None)
def main(machine, runtime, model, extra_args):

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
        elif extra_args == "gpu":
            config = get_machine_config(machine, runtime)
            setup_environment(machine, model_pairs[0])
        elif extra_args == "webui":  
            config = get_machine_config(machine, runtime)
            if runtime == "ollama":
                setup_environment(machine, ["test", "test"])
            elif runtime == "vllm":
                setup_environment(machine, model_pairs[i])

        os.environ["SERVER_IMAGE"] = config.get("server_image", "")
        os.environ["SERV_VOL"] = config.get("server_vol", "")
        os.environ["HOST_SOCK"] = config.get("host_sock", "")

        if extra_args == "webui":
            webui = True
        else:
            webui = False

        if model == "variable":
            render_templates(machine, runtime, model_pairs[i][1], webui=webui)
        elif runtime == "variable":
            render_templates(machine, rt, model_pairs[0][1], webui=webui)
        elif machine == "variable":
            render_templates(m, runtime, model_pairs[0][1], webui=webui)
        elif extra_args == "gpu":
            gpu_used = False if i == 0 else True
            render_templates(machine, runtime, model_pairs[0][1], gpu=gpu_used, webui=webui)
        else:
            render_templates(machine, runtime, model_pairs[i][1], webui=webui)

        run(config["command"])

if __name__ == '__main__':
    main()