from prometheus_client import start_http_server, Gauge
import random
import time
import podman
import os

podman_client = podman.PodmanClient(base_url="unix:///tmp/podman.sock")

containers = podman_client.containers.list()

stats = [None, None]

CPU_USAGE = [Gauge('cpu_usage_one', 'CPU ....'), Gauge('cpu_usage_two', 'CPU ....')]
MEM_USAGE = [Gauge('mem_usage_one', 'Mem ....'), Gauge('mem_usage_two', 'Mem ....')]
AVG_CPU_USAGE = [Gauge('avg_cpu_usage_one', 'CPU ....') , Gauge('avg_cpu_usage_two', 'CPU ....')]

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(8000)
    # Generate some requests.
    iter = int(os.environ.get("ITER", "Error"))

    for container in containers:
        if container.name == "ollama-server":
            stats[iter] = container.stats(stream=True, decode=True)

    for stat in stats[iter]:
        CPU_USAGE[iter].set(stat["Stats"][0].get("CPU"))
        MEM_USAGE[iter].set(stat["Stats"][0].get("MemUsage"))
        AVG_CPU_USAGE[iter].set(stat["Stats"][0].get("AvgCPU"))
        time.sleep(0.5)