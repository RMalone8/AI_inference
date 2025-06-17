import click
from invoke import run
import os

@click.command()
@click.option('--machine', help='The machine to deploy the modles onto')

def main(machine):
    if machine == "armchair":
        command = "sh startup.sh"
        ollama_image = "docker.io/ollama/ollama:latest"
        server_vol = "ollama_models:/root/.ollama"
        host_sock = "/run/user/1001/podman/podman.sock"
        os.environ["CONTAINER_HOST"] = "ssh://ryan@ewr0.nichi.link:9022/run/user/1001/podman/podman.sock"
        os.environ["CONTAINER_SSHKEY"] = "/Users/rmalone/.ssh/id_ed25519"
    elif machine == "jetson":
        ollama_image = "docker.io/dustynv/ollama:0.6.8-r36.4-cu126-22.04"
        server_vol = "ollama:/data/models/ollama"
        host_sock = "/run/podman/podman.sock"
        command = "python jetson.py"
        #os.environ["OLLAMA_IMAGE"] = "docker.io/dustynv/ollama:0.6.8-r36.4-cu126-22.04"
    else:
        command = "echo 'No machine chosen'"

    os.environ["OLLAMA_IMAGE"] = ollama_image
    os.environ["SERV_VOL"] = server_vol
    os.environ["HOST_SOCK"] = host_sock

    run(command)

if __name__ == '__main__':
    main()