import re, json, sys

def parse_weibo_ajax(text):
    try:
        res_json = json.loads(text)
        html = res_json['data']
    except:
        if re.search(r'\"data\"\:\"', text):
            return 2
        print("unsuccess in weibo ajax")
        return 1
    return 0


with open('debug.json', 'r') as f:
    str = f.read()

res = parse_weibo_ajax(str)
print(res)
