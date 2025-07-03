After getting a lease with jumpstarter for the Jetson, manually power cycle the machine or set `POWERCYCLE=True` in jetson.py.

run.py will run the project and accepts options that will allow you to determine what differs between deployments.

`uv run python run.py --model variable` will compare different models (vllm by default), running them consecutively.

Line 57 on jetson.py: `os.environ["CONTAINER_SSHKEY"] = "/Users/rmalone/.ssh/id_ed25519"` will have to be configured for your device.