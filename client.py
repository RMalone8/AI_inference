# /// script
# dependencies = [
#   "pydantic",
#   "langchain[openai]",
# ]
# ///


from langchain_openai import ChatOpenAI


#from langchain_core.messages import HumanMessage, SystemMessage

#from pydantic import BaseModel, Field

#import base64
#from pathlib import Path

import subprocess
import os
import time

ITER_NO = 10

def main():
    model_name = os.environ.get("CLIENT_TYPE", "Cannot Find Model Name")

    while subprocess.run(["ollama", "list"], capture_output=True).returncode != 0:
        time.sleep(5)

    prompt = ["ollama", "run", model_name, "'What breed of cat is in /tmp/cat.jpg and does the cat look dangerous?'"]

    for _ in range(ITER_NO):
        subprocess.run(["curl", "https://cataas.com/cat", "-o", "/tmp/cat.jpg"])
        subprocess.run(prompt)

if __name__ == "__main__":
    main()