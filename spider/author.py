import json
import re

import requests
from fake_useragent import UserAgent

from tools import RedisConnectionPool, get_proxy


class Author:
    def __init__(self, author_url):
        """
        :param author_url: 类似博主的名称 例如：/@xxx
        """
        self.author_url = author_url
        self.redis = RedisConnectionPool().get_client()
        self.ua = UserAgent()
        self.base_url = "https://www.youtube.com"

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

    def parse(self, response: str):
        data = re.findall('var ytInitialData = ({.+?});', response)
        if data:
            data = json.loads(data[0])
        # 解析订阅者数量

        # 解析视频名称

        # 获取到每一个视频的链接

        # 通过视频id 进行热门推荐，得到相应博主的id，循环即可

        #

    def get_author_info(self):
        url = self.base_url + self.author_url + "/videos"
        response = requests.get(url, headers=self.get_headers(), proxies=get_proxy())
