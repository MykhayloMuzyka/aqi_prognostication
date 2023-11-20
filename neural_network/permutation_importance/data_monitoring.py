import pickle
import matplotlib.pyplot as plt
import pandas as pd
from nn import prepare_data

data = []
with open(f'importances_final/imp.pickle', 'rb') as f:
    data.append(dict([(j[1], j[0]) for j in list(pickle.load(f))]))

avg_data = {}
for key in data[0].keys():
    temp_data = [d[key] for d in data if d[key]]
    avg_data[key] = (sum(temp_data) / len(temp_data)) if temp_data else 0

sorted_data = sorted(list(avg_data.items()), key=lambda x: x[1], reverse=True)
objects = {}
for d in sorted_data:
    if d[0].endswith('00'):
        if '\n'.join(d[0].split('_')[:-1]) not in objects:
            objects['\n'.join(d[0].split('_')[:-1])] = [d[1]]
        else:
            objects['\n'.join(d[0].split('_')[:-1])].append(d[1])

sorted_data = {}
for key, val in objects.items():
    sorted_data[key] = sum(val) / 20

sorted_objects = sorted(list(sorted_data.items()), key=lambda x: x[1], reverse=True)

for i, j in enumerate(sorted_objects):
    print(i+1, j)

axs, fig = plt.subplots(figsize=(15, 18))
plt.bar([i[0] for i in sorted_objects][:5],
        [i[1] for i in sorted_objects][:5])
plt.xticks(rotation=45, fontsize=20)
plt.yticks(fontsize=20)
plt.savefig('plt.png')
plt.show()

