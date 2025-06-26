import click
from invoke import run
from jinja2 import Environment, FileSystemLoader
import os
import yaml

@click.command()
@click.option('--machine', help='The machine to deploy the models onto')
@click.option('--runtime', help='The runtime to serve the models on')

def main(machine, runtime):

    config_dir = f"{os.path.dirname(os.path.abspath(__file__))}/remote_config"
    env = Environment(loader=FileSystemLoader(config_dir))
    template_compose = env.get_template("remote_compose.j2")
    template_prom = env.get_template("remote_prom_config.j2")

    if machine == "armchair":
        if runtime == "ollama":
            server_image = "docker.io/ollama/ollama:latest"
            server_vol = "ollama_models:/root/.ollama"
            host_sock = "/run/user/1001/podman/podman.sock"
        elif runtime == "vllm":
            server_image = "public.ecr.aws/q9t5s3a7/vllm-cpu-release-repo:v0.9.1"
            server_vol = "vllm_cache:/root/.cache/huggingface"
            host_sock = "/run/user/1001/podman/podman.sock"
        else:
            command = "echo 'No runtime chosen'"
        os.environ["CONTAINER_HOST"] = "ssh://ryan@ewr0.nichi.link:9022/run/user/1001/podman/podman.sock"
        os.environ["CONTAINER_SSHKEY"] = "/Users/rmalone/.ssh/id_ed25519"
        command = "sh startup.sh"
    elif machine == "jetson":
        if runtime == "ollama":
            server_image = "docker.io/dustynv/ollama:0.6.8-r36.4-cu126-22.04"
            server_vol = "ollama:/data/models/ollama"
            host_sock = "/run/podman/podman.sock"
            command = "python jetson.py"
        elif runtime == "vllm":
            server_image ="docker.io/dustynv/vllm:0.8.6-r36.4-cu128-24.04"
            server_vol = "vllm_cache:/root/.cache/huggingface"
            host_sock = "/run/podman/podman.sock"
            command = "python jetson.py"
        else:
            command = "echo 'No runtime chosen'"
    else:
        command = "echo 'No machine chosen'"

    models_file = f"{os.path.dirname(os.path.abspath(__file__))}/models.yaml"
    with open(models_file, 'r') as f:
        models_config = yaml.safe_load(f)
    
    model_pairs = []
    for model_key, model_data in models_config['models'].items():
        for variant_key, variant_data in model_data['variants'].items():
            if runtime in variant_data:
                model_name = variant_data[runtime]['name']
                display_name = variant_data['display_name']
                model_pairs.append(f"{display_name}:{model_name}")
    
    os.environ["MODEL_PAIRS"] = ",".join(model_pairs)

    rendered_compose = template_compose.render({"machine":machine, "runtime":runtime})
    rendered_prom = template_prom.render({"machine":machine, "runtime":runtime})

    os.environ["SERVER_IMAGE"] = server_image
    os.environ["SERV_VOL"] = server_vol
    os.environ["HOST_SOCK"] = host_sock
    
    # Set HuggingFace token if available (needed for some vLLM models)
    if "HF_TOKEN" in os.environ:
        os.environ["HF_TOKEN"] = os.environ["HF_TOKEN"]

    with open("remote_config/remote_compose.yaml", "w") as f:
        f.write(rendered_compose)
    with open("remote_config/remote_prom_config.yml", "w") as f:
        f.write(rendered_prom)

    run(command)

if __name__ == '__main__':
    main()