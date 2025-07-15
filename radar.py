import plotly.graph_objects as go
import json

categories = ['power_variance', 'gpu_memory', 'power_consumption']

fig = go.Figure()

with open('results/results.json', 'r') as f:
    results = json.load(f)

#stack1 = results['stacks']['stack1']
stack2 = results['stacks']['stack2']

max_values = results['max_values']
min_values = results['min_values']


# fig.add_trace(go.Scatterpolar(
#       r=[int(stack1['data']['power_variance'][0]['value'][1]) / max_values['power_variance'], int(stack1['data']['gpu_memory'][0]['value'][1]) / max_values['gpu_memory'], int(stack1['data']['power_consumption'][0]['value'][1]) / max_values['power_consumption']],
#       theta=categories,
#       fill='toself',
#       name='Stack 1'
# ))
fig.add_trace(go.Scatterpolar(
      r=[float(stack2['data']['power_variance'][0]['value'][1]) / max_values['power_variance'], int(stack2['data']['gpu_memory'][0]['value'][1]) / max_values['gpu_memory'], float(stack2['data']['power_consumption'][0]['value'][1]) / max_values['power_consumption']],
      theta=categories,
      fill='toself',
      name='Stack 2'
))

fig.update_layout(
  polar=dict(
    radialaxis=dict(
      visible=True,
      range=[0, 1]
    )),
  showlegend=True
)

fig.show()