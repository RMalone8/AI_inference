import sys
import os
import ast
import yaml

from jumpstarter_driver_network.adapters import FabricAdapter, TcpPortforwardAdapter

from jumpstarter.utils.env import env

from fabric import Config, Connection
from invoke import run

HOSTNAME = "localhost"
USERNAME = "admin"
PASSWORD = "passwd"
POWERCYCLE = os.environ.get("POWERCYCLE", "False").lower() # set this to true when you first get the lease
WEBUI = os.environ.get("WEBUI", "False").lower()
SERVER_PORT = ast.literal_eval(os.environ.get("SERVER_PORT", "-1"))

def get_machine_config():
    yaml_file = f"{os.path.dirname(os.path.abspath(__file__))}/run_config.yaml"
    with open(yaml_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config

def jmp_connection(config):
    # init jumpstarter client from env (jmp shell)
    with env() as dut:
        if POWERCYCLE == "true":
            # ensure the usb drive is connected to the dut
            dut.storage.dut()

            # open serial console
            with dut.serial.pexpect() as p:
                # forward console output to stdout
                p.logfile = sys.stdout.buffer

                # power cycle dut
                dut.power.cycle()

                # wait for firmware
                p.expect_exact("Enter to continue boot.", timeout=120)
                p.sendline("")

                # wait for login prompt
                p.expect_exact("login: ", timeout=120)
                p.sendline(USERNAME)
                p.expect_exact("Password: ", timeout=120)
                p.sendline(PASSWORD)
                p.expect_exact(f"[{USERNAME}@{HOSTNAME} ~]$", timeout=120)

        # connect to ssh
        with FabricAdapter(
            client=dut.ssh,
            user=USERNAME,
            config=Config(overrides={'sudo': {'password': PASSWORD}}),
            connect_kwargs={
                "password": PASSWORD,
            },
        ) as ssh:
            # run command over ssh
            #ssh.sudo("systemctl enable --now podman.socket")
            ssh.sudo("chmod -R 0777 /run/podman")
            # ssh.shell()
            if WEBUI == "true":
                with ssh.forward_remote(9090, 9090, local_host="0.0.0.0", remote_host="0.0.0.0"), ssh.forward_local(local_port=11440, remote_port=SERVER_PORT, local_host="0.0.0.0", remote_host="0.0.0.0"):
                    print(f"SERVER_PORT: {SERVER_PORT}")
                    with TcpPortforwardAdapter(client=dut.ssh) as addr:
                        os.environ["CONTAINER_HOST"] = f"ssh://root@{addr[0]}:{addr[1]}/run/podman/podman.sock"
                        os.environ["CONTAINER_SSHKEY"] = config['ssh_key']
                        run("podman images")
                        run("./startup.sh")
            else:
                with ssh.forward_remote(9090, 9090, local_host="0.0.0.0", remote_host="0.0.0.0"):
                    with TcpPortforwardAdapter(client=dut.ssh) as addr:
                        os.environ["CONTAINER_HOST"] = f"ssh://root@{addr[0]}:{addr[1]}/run/podman/podman.sock"
                        os.environ["CONTAINER_SSHKEY"] = config['ssh_key']
                        run("podman images")
                        run("./startup.sh")

def ssh_connection(config):

    os.environ["CONTAINER_HOST"] = f"ssh://{config['machine_config']['username']}@{config['machine_config']['address']}:{config['machine_config']['port']}/run/podman/podman.sock"  
    os.environ["CONTAINER_SSHKEY"] = config['ssh_key']

    with Connection(f"{config['machine_config']['username']}@{config['machine_config']['address']}", connect_kwargs={"password": config['machine_config']['password']}, port=config['machine_config']['port']) as ssh:
        if WEBUI == "true":
            with ssh.forward_remote(9090, 9090, local_host="0.0.0.0", remote_host="0.0.0.0"), ssh.forward_local(local_port=11440, remote_port=SERVER_PORT, local_host="0.0.0.0", remote_host="0.0.0.0"):
                ssh.run("podman images")
                run("sh startup.sh")
        else:
            with ssh.forward_remote(9090, 9090, local_host="0.0.0.0", remote_host="0.0.0.0"):
                ssh.run("podman images")
                run("sh startup.sh")

def main():

    config = get_machine_config()

    if config['use_jumpstarter']:
        jmp_connection(config)
    else:
        ssh_connection(config)

if __name__ == "__main__":
    main()