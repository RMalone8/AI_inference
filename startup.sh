#!/bin/bash

set -e

podman --connection podman-machine-default compose -f local_compose.yaml up --build --detach

for MODEL_NAME in moondream:1.8b llava-phi3:3.8b
do
    export MODEL_NAME
    podman --connection armchair compose -f remote_compose.yaml up --build --abort-on-container-exit
    podman --connection armchair compose -f remote_compose.yaml down
done

# for the time being, must close down grafana container on your own after the script runs