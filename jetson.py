import sys

from jumpstarter_driver_network.adapters import FabricAdapter

from jumpstarter.utils.env import env

from fabric import Config

HOSTNAME = "localhost"
USERNAME = "admin"
PASSWORD = "passwd"
POWERCYCLE = False

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
        result = ssh.sudo("podman images")
        print(result)