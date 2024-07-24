import json
import re

import requests
from jsonpath_ng import parse

url = "https://www.youtube.com/watch?v=jBjtGolcknc"
proxy = {
    'http': "http://127.0.0.1:7890",
    'https': "https://127.0.0.1:7890"
}
payload = {}
headers = {
    'authority': 'www.youtube.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
}

response = requests.request("GET", url, headers=headers, data=payload, proxies=proxy)

data = re.findall('ytInitialData = ({.+?});', response.text)
if data:
    data = json.loads(data[0])
jsonpath_expr = parse('$..url')
urls = {match.value for match in jsonpath_expr.find(data) if
        isinstance(match.value, str) and match.value.startswith('/@')}
print(urls)

jsonpath_expr = parse('$..token')
tokens = {match.value for match in jsonpath_expr.find(data) if
          isinstance(match.value, str) and "___________" in match.value}
print(tokens)

url = "https://www.youtube.com/youtubei/v1/next?prettyPrint=false"

payload = json.dumps({
    "context": {
        "client": {
            "hl": "zh-CN",
            "clientName": "WEB",
            "clientVersion": "2.20240722.00.00-canary_control_2.20240723.00.00",
            "originalUrl": "https://www.youtube.com/watch?v=jBjtGolcknc",
        }
    },
    "continuation": tokens.pop()
})
response = requests.request("POST", url, headers=headers, data=payload, proxies=proxy)
jsonpath_expr = parse('$..url')
urls = {match.value for match in jsonpath_expr.find(response.json()) if
        isinstance(match.value, str) and match.value.startswith('/@')}
print(urls)
