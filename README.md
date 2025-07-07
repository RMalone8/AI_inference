# AI Inference - A methodology for testing and comparing metrics of various AI stacks

The project displays on a Grafana Dashboard an array of metrics including:
- Power Consumption
- Memory Usage
- CPU Usage
- Latency/Throughput (Vllm only)

Right now, the project is configured for Jetson machines only

## Installation and Setup

- Must have [Jumpstarter](https://jumpstarter.dev/main/) installed

After cloning this repo, get a lease with Jumpstarter:

`uv run jmp shell -l board=orin-agx`

Then, you will have to configure line 57 on jetson.py for the path to your ssh key:

`os.environ["CONTAINER_SSHKEY"] = "/Users/rmalone/.ssh/id_ed25519"`

### Running the Project

`python run.py` will by default deploy gemma3:4b with ollama on the jetson, but additional options exist to control for different layers of the stack.

For example, if you wanted to have the model change between deployments, add `--model variable`

#### After getting the lease, you will have to add `--powercycle True` the first time you run the project

Once running, metrics will be visible on port 3000