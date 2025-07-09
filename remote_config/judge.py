# /// script
# dependencies = [
#   "pydantic",
#   "langchain[openai]",
#   "requests",
#   "prometheus_client",
# ]
# ///

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from pydantic import BaseModel, Field
from prometheus_client import start_http_server, Gauge

import base64
from pathlib import Path

import os
import time
import requests


ITER_NO = 20

class Score(BaseModel):
    score: int = Field(description="The final score of the model's description, between 0 and 100")

SYSTEM = SystemMessage(
    "You are a judge for a cat classification contest. You will be given a cat image and a description of the cat. You will need to judge how well the model's description matches the image. You will provide a score between 0 and 100, where 100 is the best score. Be critical and provide a score of 0 if the model's description does not match the image at all."
)

def main():

    start_http_server(6000)

    model_specs = os.environ.get("CLIENT_SPECS", "Cannot Find Model Specs")
    api_key = "key"
    base_url = "http://google.com"
    model_name = "gpt-4o-mini"

    client_scores = Gauge(f'client_scores_{model_specs}', 'The scores from the judge of the client')
    
    model = ChatOpenAI(
        model=model_name,
        temperature=0,
        base_url=base_url,
        api_key=api_key,
    ).with_structured_output(Score)

    for i in range(ITER_NO):
        r = requests.get('https://cataas.com/cat')
        r.raise_for_status()
        print(f"ITER: {i}")
        print(f"{model_name} is asked: ")
        print("Describe the breed and species of the animal in this image, return as JSON")
        print("The model returns: ")
        print(
            model.invoke(
                [
                    SYSTEM,
                    HumanMessage(
                        content=[
                            {
                                "type": "text",
                                "text": "Describe the breed and species of the animal in this image, return as JSON",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64.b64encode(r.content).decode()}"
                                }
                            },
                        ]
                    ),
                ]
            )
        )
        client_scores.set(score.score)


if __name__ == "__main__":
    main()