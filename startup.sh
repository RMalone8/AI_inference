#!/bin/bash

set -e

podman --connection podman-machine-default compose -f local_config/local_compose.yaml up --build --detach

export PYTHONUNBUFFERED=1

podman network rm remote_config_default || true
podman kill -a
podman rm -a
podman-compose -f remote_config/remote_compose.yaml up --build --abort-on-container-exit
podman-compose -f remote_config/remote_compose.yaml down

sleep 10

# for the time being, must close down grafana/prometheus containers on your own after the script runs