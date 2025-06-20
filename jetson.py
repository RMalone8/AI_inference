import sys
import os

from jumpstarter_driver_network.adapters import FabricAdapter, TcpPortforwardAdapter

from jumpstarter.utils.env import env

from fabric import Config
from invoke import run
import podman

HOSTNAME = "localhost"
USERNAME = "admin"
PASSWORD = "passwd"
POWERCYCLE = True # set this to true when you first get the lease

# init jumpstarter client from env (jmp shell)
with env() as dut:
    if POWERCYCLE:
        # ensure the usb dirve is connected to the dut
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
        with ssh.forward_remote(9090, 9090, local_host="0.0.0.0", remote_host="0.0.0.0"):
            with TcpPortforwardAdapter(client=dut.ssh) as addr:
                os.environ["CONTAINER_HOST"] = f"ssh://root@{addr[0]}:{addr[1]}/run/podman/podman.sock"
                os.environ["CONTAINER_SSHKEY"] = "/Users/rmalone/.ssh/id_ed25519"
                run("podman images")
                run("./startup.sh")