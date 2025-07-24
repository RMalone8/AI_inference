from fabric import Connection
from invoke import run
import os
import ast
import yaml

HOSTNAME = "localhost"
USERNAME = "admin"
PASSWORD = "passwd"
WEBUI = os.environ.get("WEBUI", "False").lower()
SERVER_PORT = ast.literal_eval(os.environ.get("SERVER_PORT", "-1"))

def get_machine_config():
    yaml_file = f"{os.path.dirname(os.path.abspath(__file__))}/run_config.yaml"
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)

    config = data['machine_config']
    
    return config

def main():

    config = get_machine_config()

    
    os.environ["CONTAINER_HOST"] = f"ssh://{config['username']}@{config['address']}:{config['port']}/run/podman/podman.sock"  
    os.environ["CONTAINER_SSHKEY"] = config['sshkey']

    with Connection(f"{config['username']}@{config['address']}", connect_kwargs={"password": config['password']}, port=config['port']) as ssh:
        if WEBUI == "true":
            with ssh.forward_remote(9090, 9090, local_host="0.0.0.0", remote_host="0.0.0.0"), ssh.forward_local(local_port=11440, remote_port=SERVER_PORT, local_host="0.0.0.0", remote_host="0.0.0.0"):
                ssh.run("podman images")
                run("sh startup.sh")
        else:
            with ssh.forward_remote(9090, 9090, local_host="0.0.0.0", remote_host="0.0.0.0"):
                ssh.run("podman images")
                run("sh startup.sh")

if __name__ == "__main__":
    main()