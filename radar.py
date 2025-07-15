import plotly.graph_objects as go
import json

categories = ['power_stddev', 'gpu_memory', 'power_consumption', 'avg_time_per_iter', 'token_per_sec_per_iter']

fig = go.Figure()

with open('results/results.json', 'r') as f:
    results = json.load(f)

stack1 = results['stacks']['jetson_ollama_gemma3_12b_temp1']
stack2 = results['stacks']['jetson_ollama_gemma3_12b_temp0']

max_values = results['max_values']
min_values = results['min_values']


fig.add_trace(go.Scatterpolar(
      r=[float(stack1['data']['power_stddev'][0]['value'][1]) / max_values['power_stddev'], float(stack1['data']['gpu_memory'][0]['value'][1]) / max_values['gpu_memory'], float(stack1['data']['power_consumption'][0]['value'][1]) / max_values['power_consumption'], float(stack1['data']['avg_time_per_iter'][0]['value'][1]) / max_values['avg_time_per_iter'], float(stack1['data']['token_per_sec_per_iter'][0]['value'][1]) / max_values['token_per_sec_per_iter']],
      theta=categories,
      fill='toself',
      name='Stack 1'
))
fig.add_trace(go.Scatterpolar(
      r=[float(stack2['data']['power_stddev'][0]['value'][1]) / max_values['power_stddev'], float(stack2['data']['gpu_memory'][0]['value'][1]) / max_values['gpu_memory'], float(stack2['data']['power_consumption'][0]['value'][1]) / max_values['power_consumption'], float(stack2['data']['avg_time_per_iter'][0]['value'][1]) / max_values['avg_time_per_iter'], float(stack2['data']['token_per_sec_per_iter'][0]['value'][1]) / max_values['token_per_sec_per_iter'] ],
      theta=categories,
      fill='toself',
      name='Stack 2'
))

fig.update_layout(
  polar=dict(
    radialaxis=dict(
      visible=False,
      range=[0, 1]
    )),
  showlegend=True
)

fig.show()