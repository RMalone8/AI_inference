import click
from invoke import run
from jinja2 import Environment, FileSystemLoader
import os

@click.command()
@click.option('--machine', help='The machine to deploy the modles onto')

def main(machine):

    config_dir = f"{os.path.dirname(os.path.abspath(__file__))}/remote_config"
    env = Environment(loader=FileSystemLoader(config_dir))
    template = env.get_template("remote_compose.j2")

    if machine == "armchair":
        ollama_image = "docker.io/ollama/ollama:latest"
        server_vol = "ollama_models:/root/.ollama"
        host_sock = "/run/user/1001/podman/podman.sock"
        os.environ["CONTAINER_HOST"] = "ssh://ryan@ewr0.nichi.link:9022/run/user/1001/podman/podman.sock"
        os.environ["CONTAINER_SSHKEY"] = "/Users/rmalone/.ssh/id_ed25519"
        command = "sh startup.sh"
    elif machine == "jetson":
        ollama_image = "docker.io/dustynv/ollama:0.6.8-r36.4-cu126-22.04"
        server_vol = "ollama:/data/models/ollama"
        host_sock = "/run/podman/podman.sock"
        command = "python jetson.py"
    else:
        command = "echo 'No machine chosen'"

    rendered_compose = template.render({"machine":machine})

    os.environ["OLLAMA_IMAGE"] = ollama_image
    os.environ["SERV_VOL"] = server_vol
    os.environ["HOST_SOCK"] = host_sock

    with open("remote_config/remote_compose.yaml", "w") as f:
        f.write(rendered_compose)

    run(command)

if __name__ == '__main__':
    main()