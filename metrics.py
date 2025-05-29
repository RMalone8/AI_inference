from prometheus_client import start_http_server, Gauge
import random
import time
import podman

podman_client = podman.PodmanClient(base_url="unix:///tmp/podman.sock")

containers = podman_client.containers.list()

CPU_USAGE = Gauge('cpu_usage', 'CPU ....')
MEM_USAGE = Gauge('mem_usage', 'Mem ....')

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(8000)
    # Generate some requests.

    for container in containers:
        if container.name == "composetest-ollama-server-1":
            stats = container.stats(stream=True, decode=True)


    print(stats)

    for stat in stats:
        print(stat["Stats"][0])
        CPU_USAGE.set(stat["Stats"][0].get("CPU"))
        MEM_USAGE.set(stat["Stats"][0].get("MemPerc"))
        time.sleep(1)