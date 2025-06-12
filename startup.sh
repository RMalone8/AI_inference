#!/bin/bash

set -e

podman --connection podman-machine-default compose -f local_compose.yaml up --build --detach

for MODEL_PAIR in "gemma3_4b:gemma3:4b" "gemma3_12b:gemma3:12b"
do

    MODEL_NAME="${MODEL_PAIR%%:*}"
    MODEL_SPECS="${MODEL_PAIR#*:}"
    export OLLAMA_IMAGE="docker.io/dustynv/ollama:0.6.8-r36.4-cu126-22.04"

    export MODEL_NAME
    export MODEL_SPECS
    podman-compose --no-ansi -f remote_compose.yaml up   --no-color --build --abort-on-container-exit
    podman-compose --no-ansi -f remote_compose.yaml down --no-color

    sleep 10

done

# for the time being, must close down grafana container on your own after the script runs