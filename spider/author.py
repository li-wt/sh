import json
import re
from jsonpath_ng.ext import parse

import requests
from fake_useragent import UserAgent

from db.mysql_db import AsyncMySQLManager
from db.redis_db import RedisDb
from loguru import logger


class Author:
    def __init__(self):
        """
        :param author_url: 类似博主的名称 例如：/@xxx
        """
        self.mysql_db = AsyncMySQLManager()
        self.redis_db = RedisDb()
        
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
    
    def next_similar(self, token: str, author_id: str):
        url = "https://www.youtube.com/youtubei/v1/browse"
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
        self.parse(response.json(), author_id)
    
    def save_watch_id(self, data: list):
        sql = 'insert into watch(watch) values (%s)'
        for watch_id in data:
            if self.mysql_db.process_url(sql=sql, data=watch_id):
                self.redis_db.lpush("watch_id", watch_id)
    
    def save_title(self, name: str, data: dict):
        """这里数据存储只能正确，错误逻辑怎么实现，未写代码。逻辑，存储三次，如果失败将用户名从mysql删除，添加到redis中即可"""
        sql = 'insert into title(name, title) values (%s, %s)'
        if self.mysql_db.insert_url(sql=sql, data=[name, data]):
            logger.info(f'存储成功，{name}')
    
    def parse(self, response: str, author_id: str):
        data = re.findall('var ytInitialData = ({.+?});', response)
        if data:
            data = json.loads(data[0])
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
                break
            watch_id = parse('$..richItemRenderer.content.videoRenderer.videoId').find(content)[0].value
            title = parse('$..richItemRenderer.content.videoRenderer.title.runs[*].text').find(content)[0].value
            watch_list.append(watch_id)
            title_list.append(title)
            num += 1
        
        self.save_watch_id(watch_list)
        self.save_title(name=author_id, data={"title": title_list})
        # 解析订阅者数量
        
        # 解析视频名称
        
        # 获取到每一个视频的链接
        
        # 通过视频id 进行热门推荐，得到相应博主的id，循环即可
        
        #
    
    def get_author_info(self, author_id: str):
        url = self.base_url + author_id + "/videos"
        response = requests.get(url, headers=self.get_headers(), verify=False)
        self.parse(response.text, author_id)


if __name__ == '__main__':
    Author().get_author_info(author_id='/@dailylofiradio')
