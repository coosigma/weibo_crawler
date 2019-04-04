import re, json, sys

data = []
with open('test_data.json', 'r') as f:
    line = f.readline()
    data.append(json.loads(line))

print(data[0])
