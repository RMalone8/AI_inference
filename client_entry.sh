#!/bin/bash
set -e

echo 'Waiting for Ollama server to be ready...'
while ! ollama --host=$OLLAMA_HOST:11434 list > /dev/null 2>&1; do
  sleep 5
done

echo 'Ollama server is ready. Pulling llava-phi3:3.8b model... (This may take a while)'
ollama --host=$OLLAMA_HOST:11434 pull llava-phi3:3.8b || true

echo 'Running llava-phi3:3.8b model with a simple prompt:'
ollama --host=$OLLAMA_HOST:11434 run llava-phi3:3.8b 'What breed of cat is at /tmp/cat.jpg?'