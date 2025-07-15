from langchain_core.messages.ai import AIMessage
import json

print(AIMessage(content="Hello, world!"))

message = '''content='```json\n{\n  "species": "Cat",\n  "breed": "Likely Siberian or Norwegian Forest Cat",\n  "description": "This cat exhibits several characteristics typical of Siberian or Norwegian Forest Cats. The most notable features are the long, thick, semi-long fur, bushy tail, and a substantial ruff around the neck. The coat pattern appears to be a tabby (classic or mackerel), with a mix of gray and brown markings. The large, expressive eyes are a striking feature. While a definitive breed identification is difficult without more information, the combination of these traits strongly suggests one of these two breeds."\n}\n```' additional_kwargs={'refusal': None} response_metadata={'token_usage': {'completion_tokens': 133, 'prompt_tokens': 378, 'total_tokens': 511, 'completion_tokens_details': None, 'prompt_tokens_details': None}, 'model_name': 'gemma3:12b', 'system_fingerprint': 'fp_ollama', 'id': 'chatcmpl-415', 'service_tier': None, 'finish_reason': 'stop', 'logprobs': None} id='run--0085db33-eb9c-4778-83ba-893f6dc34518-0' usage_metadata={'input_tokens': 378, 'output_tokens': 133, 'total_tokens': 511, 'input_token_details': {}, 'output_token_details': {}}'''
print(AIMessage().response_metadata)
print(type(AIMessage(content=content).content))
content_json = json.loads(AIMessage(content=content).content.strip("```json\n").strip("```"))
