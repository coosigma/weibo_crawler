import re, json, sys

data = []
with open(sys.argv[1], 'r') as f:
    for line in f:
        data.append(json.loads(line))

for e in data:
    print(e)
