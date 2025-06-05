#!/bin/bash

set -e

podman --connection podman-machine-default compose -f local_compose.yaml up --build --detach

for MODEL_PAIR in "moondream:moondream:1.8b" "llava:llava-phi3:3.8b"
do

    MODEL_NAME="${MODEL_PAIR%%:*}"
    MODEL_SPECS="${MODEL_PAIR#*:}"

    export MODEL_NAME
    export MODEL_SPECS
    podman --connection armchair compose -f remote_compose.yaml up --build --abort-on-container-exit
    podman --connection armchair compose -f remote_compose.yaml down

    sleep 10

done

# for the time being, must close down grafana container on your own after the script runs