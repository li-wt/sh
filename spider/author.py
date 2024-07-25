import asyncio
import json
import re

import requests
from fake_useragent import UserAgent
from jsonpath_ng.ext import parse
from loguru import logger

import tools
from db.mysql_db import AsyncMySQLManager
from db.redis_db import RedisDb


class Author:
    def __init__(self):
        """
        :param author_url: 类似博主的名称 例如：/@xxx
        """
        self.flag = False
        self.client = tools.AsyncHttpClient()
        self.mysql_db = AsyncMySQLManager()
        self.redis_db = RedisDb()
        self.proxy = tools.get_proxy
        self.ua = UserAgent()
        self.base_url = "https://www.youtube.com"

    async def get_proxy(self):
        return {
            'http': "http://127.0.0.1:7890",
            'https': "https://127.0.0.1:7890"
        }

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

    async def next_similar(self, token: str, author_id: str):
        url = "https://www.youtube.com/youtubei/v1/browse"
        payload = json.dumps({
            "context": {
                "client": {
                    "hl": "zh-CN",
                    "clientName": "WEB",
                    "clientVersion": "2.20240724.00.00",
                },
            },
            "continuation": token
        })
        response = requests.request("POST", url, headers=await self.get_headers(), data=payload,
                                    proxies=await self.get_proxy())
        if response.status_code == 200:
            await self.parse(json.loads(response), author_id)
        print(response.text)
        logger.info(f'状态码{response.status_code}')

    async def save_watch_id(self, data: list):
        sql = 'insert into watch(watch) values (%s)'
        for watch_id in data:
            if await self.mysql_db.process_url(sql=sql, data=watch_id):
                await self.redis_db.lpush("watch_id", watch_id)

    async def save_title(self, name: str, data: dict):
        """这里数据存储只能正确，错误逻辑怎么实现，未写代码。逻辑，存储三次，如果失败将用户名从mysql删除，添加到redis中即可"""
        sql = 'insert into title(name, `title`) values (%s, %s)'
        if await self.mysql_db.insert_url(sql=sql, data=[name, json.dumps(data, ensure_ascii=False)]):
            logger.info(f'存储成功，{name}')

    async def parse(self, response: str or dict, author_id: str):
        logger.info(f'解析用户-->{author_id}')
        if type(response) == str:
            data = re.findall('var ytInitialData = ({.+?});', response)
            if data:
                data = json.loads(data[0])
        else:
            data = response
        item = \
            parse("$.contents.twoColumnBrowseResultsRenderer.tabs[?(@.tabRenderer.title == '视频')].tabRenderer").find(
                data)[
                0].value

        contents = parse('@.content.richGridRenderer.contents').find(item)[0].value
        num = 0
        watch_list = []
        title_list = []
        for content in contents[:-1]:
            if num == 20:
                self.flag = True
                break
            watch_id = parse('$..richItemRenderer.content.videoRenderer.videoId').find(content)[0].value
            title = parse('$..richItemRenderer.content.videoRenderer.title.runs[*].text').find(content)[0].value
            watch_list.append(watch_id)
            title_list.append(title)
            num += 1

        await self.save_watch_id(watch_list)
        await self.save_title(name=author_id, data={"title": title_list})
        if self.flag:
            return
        # 获取下一页的token
        continue_data = contents[-1]
        token = parse('$..continuationItemRenderer.continuationEndpoint.continuationCommand.token').find(continue_data)[
            0].value
        # 第一页的数量就能达到20 下一页逻辑不在处理，下一页需要重新写解析函数，和第一页的结构不太一样
        if not token:
            logger.info('没有下一页')
            return
        await self.next_similar(token=token, author_id=author_id)

    async def back_fill(self, author_id: str) -> None:
        logger.error(f'请求失败:-----> author_id:{author_id},执行回填')
        re_try = 0
        while re_try < 3:
            try:
                await self.redis_db.lpush('author_id', author_id)
                logger.error(f'回填成功:-----> watch_id:{author_id}')
                return
            except Exception:
                re_try += 1
                logger.error(f'回填失败:-----> author_id:{author_id},重试次数：{3 - re_try}')

    async def get_author_info(self, author_id: str):

        url = self.base_url + author_id + "/videos"
        response = await self.client.get(url=url, headers=await self.get_headers())
        await self.parse(response, author_id)

    async def run(self):
        await self.mysql_db.init_pool()
        await self.redis_db.init()
        await self.client.init()

        while True:
            author_id = await self.redis_db.rpop('author_id')
            if not author_id:
                logger.info('没有author_id，休息中')
                await asyncio.sleep(60)
            try:
                logger.info(f'开始获取{author_id}用户')
                await self.get_author_info(author_id=author_id)
            except Exception as e:
                await self.back_fill(author_id=author_id)


if __name__ == '__main__':
    asyncio.run(Author().run())
    # Author().get_author_info(author_id='/@dailylofiradio')
