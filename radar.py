import plotly.graph_objects as go
import json
import math

categories = ['Power Consumption Stability', 'GPU Memory Usage', 'Power Consumption', 'Request Latency', 'Output Tokens Per Second', 'CPU Usage', 'CPU Usage Stability']

fig = go.Figure()

with open('results/results.json', 'r') as f:
    results = json.load(f)

stack_names = ["jetson_vllm_granite3_2_2b", "jetson_ollama_granite3_2_2b"]

stack1 = results['stacks'][stack_names[0]]
stack2 = results['stacks'][stack_names[1]]

max_values = results['max_values']
min_values = results['min_values']

stack1_data = [1 - float(stack1['data']['power_stddev'][0]['value'][1]) / max_values['power_stddev'], 
        1 - float(stack1['data']['gpu_memory'][0]['value'][1]) / max_values['gpu_memory'], 
        1 - float(stack1['data']['power_consumption'][0]['value'][1]) / max_values['power_consumption'], 
        1 - float(stack1['data']['avg_time_per_iter'][0]['value'][1]) / max_values['avg_time_per_iter'], 
        float(stack1['data']['token_per_sec_per_iter'][0]['value'][1]) / max_values['token_per_sec_per_iter'],
        1 - float(stack1['data']['avg_cpu_usage'][0]['value'][1]) / max_values['avg_cpu_usage'],
        1 - float(stack1['data']['cpu_usage_stddev'][0]['value'][1]) / max_values['cpu_usage_stddev']]

stack1_data = [math.sqrt(x) for x in stack1_data]

stack2_data = [1 - float(stack2['data']['power_stddev'][0]['value'][1]) / max_values['power_stddev'], 
        1 - float(stack2['data']['gpu_memory'][0]['value'][1]) / max_values['gpu_memory'], 
        1 - float(stack2['data']['power_consumption'][0]['value'][1]) / max_values['power_consumption'], 
        1 - float(stack2['data']['avg_time_per_iter'][0]['value'][1]) / max_values['avg_time_per_iter'], 
        float(stack2['data']['token_per_sec_per_iter'][0]['value'][1]) / max_values['token_per_sec_per_iter'],
        1 - float(stack2['data']['avg_cpu_usage'][0]['value'][1]) / max_values['avg_cpu_usage'],
        1 - float(stack2['data']['cpu_usage_stddev'][0]['value'][1]) / max_values['cpu_usage_stddev']]

stack2_data = [math.sqrt(x) for x in stack2_data]


fig.add_trace(go.Scatterpolar(
      r=stack1_data,
      theta=categories,
      fill='toself',
      name=stack_names[0]
))
fig.add_trace(go.Scatterpolar(
      r=stack2_data,
      theta=categories,
      fill='toself',
      name=stack_names[1]
))

fig.update_layout(
  polar=dict(
    radialaxis=dict(
      visible=True,
      range=[0, 1]
    )),
  showlegend=True,
  font=dict(
    size=20
  )
)

fig.show()