from prometheus_client import start_http_server, Gauge
import random
import time
import podman

podman_client = podman.PodmanClient(base_url="unix:///tmp/podman.sock")

containers = podman_client.containers.list()

CPU_USAGE1 = Gauge('cpu_usage_llava_phi', 'CPU ....')
MEM_USAGE1 = Gauge('mem_usage_llava_phi', 'Mem ....')
AVG_CPU_USAGE1 = Gauge('avg_cpu_usage_llava_phi', 'CPU ....')
CPU_USAGE2 = Gauge('cpu_usage_moondream', 'CPU ....')
MEM_USAGE2 = Gauge('mem_usage_moondream', 'Mem ....')
AVG_CPU_USAGE2 = Gauge('avg_cpu_usage_moondream', 'CPU ....')

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(8000)
    # Generate some requests.

    for container in containers:
        if container.name == "composetest-ollama-server-llava-phi-1":
            stats1 = container.stats(stream=True, decode=True)
        if container.name == "composetest-ollama-server-moondream-1":
            stats2 = container.stats(stream=True, decode=True)

    for stat1, stat2 in zip(stats1, stats2):
        CPU_USAGE1.set(stat1["Stats"][0].get("CPU"))
        MEM_USAGE1.set(stat1["Stats"][0].get("MemUsage"))
        AVG_CPU_USAGE1.set(stat1["Stats"][0].get("AvgCPU"))
        CPU_USAGE2.set(stat2["Stats"][0].get("CPU"))
        MEM_USAGE2.set(stat2["Stats"][0].get("MemUsage"))
        AVG_CPU_USAGE2.set(stat2["Stats"][0].get("AvgCPU"))
        #print(stat1)
        time.sleep(0.5)