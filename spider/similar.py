import asyncio
import json
import re
import time

from db.mysql_db import AsyncMySQLManager
import requests
from fake_useragent import UserAgent
from jsonpath_ng import parse
from loguru import logger
from db.redis_db import RedisDb


class Similar:
    def __init__(self, max_page: int = 0):
        """
        author_url: 类似博主的名称 例如：/@xxx
        """
        self.mysql_db = AsyncMySQLManager()
        self.redis_db = RedisDb()
        self.max_page = max_page
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
            'user-agent': self.ua.random
        }
        return headers
    
    async def get_watch(self, watch_id):
        response = requests.request("GET", self.base_url + watch_id, headers=self.get_headers(),
                                    verify=False).content.decode('utf-8')
        data = re.findall('ytInitialData ?= ?({.+?});', response)
        if data:
            data = json.loads(data[0])
        await self.parse(data)
    
    async def save(self, data: list):
        """保存id"""
        sql = 'insert into url(url) values (%s)'
        for item in data:
            if await self.mysql_db.process_url(sql=sql, data=[item]):
                await self.redis_db.lpush('author_id', item)
    
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
                    "originalUrl": f"https://www.youtube.com",
                }
            },
            "continuation": token
        })
        response = requests.request("POST", url, headers=self.get_headers(), data=payload,
                                    verify=False)
        await self.parse(response.json())
    
    async def run(self):
        await self.redis_db.init()
        await self.mysql_db.init_pool()
        while True:
            watch_id = await self.redis_db.rpop('watch_id')
            if not watch_id:
                logger.info('相似视频watch_id没有，休息中')
                time.sleep(60)
            try:
                await self.get_watch(watch_id)
            except Exception as e:
                await self.back_fill(watch_id=watch_id)
    
    async def back_fill(self, watch_id: str) -> None:
        logger.error(f'请求失败:-----> watch_id:{watch_id},执行回填')
        re_try = 0
        while re_try < 3:
            try:
                await self.redis_db.lpush('watch_id', watch_id)
                logger.error(f'回填成功:-----> watch_id:{watch_id}')
                return
            except Exception:
                re_try += 1
                logger.error(f'回填失败:-----> watch_id:{watch_id},重试次数：{3 - re_try}')


if __name__ == '__main__':
    asyncio.run(Similar(max_page=0).save(data=['2GsRDYag9jI']))
