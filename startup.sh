#!/bin/bash

set -e

podman --connection podman-machine-default compose -f local_config/local_compose.yaml up --build --detach

for MODEL_PAIR in "gemma3_4b:gemma3:4b" "gemma3_12b:gemma3:12b"
do

    MODEL_NAME="${MODEL_PAIR%%:*}"
    MODEL_SPECS="${MODEL_PAIR#*:}"

    export MODEL_NAME
    export MODEL_SPECS

    podman network rm remote_config_default || true
    podman kill -a
    podman rm -a
    podman-compose -f remote_config/remote_compose.yaml up --build --abort-on-container-exit
    podman-compose -f remote_config/remote_compose.yaml down

    sleep 10

done

# for the time being, must close down grafana container on your own after the script runs