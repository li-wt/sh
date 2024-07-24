import asyncio
import json
import re
from db.mysql_db import AsyncMySQLManager
import requests
from fake_useragent import UserAgent
from jsonpath_ng import parse
from tools import RedisConnectionPool, get_proxy


class Similar:
    def __init__(self, watch_id: str, max_page):
        """
        :param author_url: 类似博主的名称 例如：/@xxx
        """
        self.max_page = max_page
        self.watch_id = watch_id
        self.redis = RedisConnectionPool().get_client()
        self.ua = UserAgent()
        self.base_url = "https://www.youtube.com/watch?v="
        self.page = 0
    
    async def get_headers(self):
        headers = {
            'authority': 'www.youtube.com',
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://www.youtube.com',
            'referer': 'https://www.youtube.com',
            'user-agent':  self.ua.random
        }
        return headers
    
    async def get_watch(self):
        response = requests.request("GET", self.base_url + self.watch_id, headers=self.get_headers(),
                                    verify=False).content.decode('utf-8')
        data = re.findall('ytInitialData ?= ?({.+?});', response)
        if data:
            data = json.loads(data[0])
        await self.parse(data)
    
    async def save(self, data: list):
        """保存id"""
        pass
    
    async def parse(self, data: dict):
        """
        :param data:
        :return:
        data 给author类
        """
        jsonpath_expr = parse('$..url')
        author_id = {match.value for match in jsonpath_expr.find(data) if
                     isinstance(match.value, str) and match.value.startswith('/@')}
        await self.save(list(author_id))
        print(author_id)
        jsonpath_expr = parse('$..button.buttonRenderer.command.continuationCommand.token')
        tokens = {match.value for match in jsonpath_expr.find(data)}
        if not tokens:
            print('没有tokens')
            return
        self.page += 1
        if self.page - self.max_page != 0:
            print(self.page)
            await self.next_similar(tokens.pop())
    
    async def next_similar(self, token):
        url = "https://www.youtube.com/youtubei/v1/next?prettyPrint=false"
        payload = json.dumps({
            "context": {
                "client": {
                    "hl": "zh-CN",
                    "clientName": "WEB",
                    "clientVersion": "2.20240722.00.00-canary_control_2.20240723.00.00",
                    "originalUrl": f"https://www.youtube.com/watch?v={self.watch_id}",
                }
            },
            "continuation": token
        })
        response = requests.request("POST", url, headers=self.get_headers(), data=payload,
                                    verify=False)
        await self.parse(response.json())


if __name__ == '__main__':
    asyncio.run(Similar(watch_id='2GsRDYag9jI', max_page=0).get_watch())
