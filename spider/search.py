import json

import requests
from fake_useragent import UserAgent
from jsonpath_ng import parse

from tools import RedisConnectionPool, get_proxy


class Search:
    def __init__(self, key_words):
        self.key_words = key_words
        self.redis = RedisConnectionPool().get_client()
        self.ua = UserAgent()
        self.base_url = "https://www.youtube.com/youtubei/v1/search?prettyPrint=false"

    def get_payload(self):
        payload = json.dumps({
            "context": {
                "client": {
                    "hl": "zh-CN",
                    "clientName": "WEB",
                    "clientVersion": "2.20240722.00.00",
                    "originalUrl": "https://www.youtube.com",
                },

            },
            "query": self.key_words,
        })
        return payload

    def get_headers(self):
        headers = {
            'authority': 'www.youtube.com',
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://www.youtube.com',
            'referer': 'https://www.youtube.com',
            'user-agent': self.ua.random
        }
        return headers

    def parse(self, response_data: str):
        data = json.loads(response_data)
        channels_info = []
        jsonpath_expr = parse('$..url')
        urls = {match.value for match in jsonpath_expr.find(data) if
                isinstance(match.value, str) and match.value.startswith('/@')}

        # 将这些用来作为一个入口

    def proper(self, author: str):
        url = 'https://youtube' + author
        requests.get(url,)
        # return channels_info

    def run(self):
        proxy = get_proxy()
        headers = self.get_headers()
        payload = self.get_payload()
        response = requests.request("POST", self.base_url, proxies=proxy, headers=headers, data=payload)
        self.parse(response.text)


if __name__ == '__main__':
    Search('python').run()
# response = requests.request("POST", url, proxies=proxy, headers=headers, data=payload)
#
# print(response.text)
