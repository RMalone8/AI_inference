import podman
import argparse

podman_client = podman.PodmanClient(base_url="unix:///run/user/1001/podman/podman.sock")

containers = podman_client.containers.list()

cpu_percent1 = []
mem_usage1 = []

def main():
    #parser = argparse.ArgumentParser()

    #parser.add_argument("--containername1", help="The name of the container to analyze")
    #parser.add_argument("--count", type=int, default=1, help="How many data points you want to collect")

    #args = parser.parse_args()


    #if args.count <= 0:
    #    raise ValueError("--count must be a positive int")

    for container in containers:
        if container.name == "ollama-server-1":
            stats = container.stats(stream=True, decode=True)

    for i, stat in enumerate(stats):
        print(i)
        cpu_percent1.append(stat["Stats"][0].get("CPU")) # seems to be different from Podman Desktop's reported usage
        mem_usage1.append(stat["Stats"][0].get("MemPerc"))
        if i + 1 == 20:
            break

if __name__ == "__main__":
    main()