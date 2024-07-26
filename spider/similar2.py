import asyncio
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from fake_useragent import UserAgent
from jsonpath_ng import parse
from loguru import logger

from db.mysql_db import AsyncMySQLManager
from db.redis_db import RedisDb
from tools import AsyncHttpClient


class Similar:
    def __init__(self, max_page: int = 0):
        self.client = AsyncHttpClient()
        self.mysql_db = AsyncMySQLManager()
        self.redis_db = RedisDb()
        self.max_page = max_page
        self.ua = UserAgent()
        self.base_url = "https://www.youtube.com/watch?v="
        self.page = 0
        self.watch_id = None
        self.source = None
        self.watch_id_set = None

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
        response = await self.client.get(self.base_url + watch_id, headers=await self.get_headers())

        data = re.findall(r'ytInitialData = ({.+?});', response, re.S)
        if data:
            data = json.loads(data[0])
        else:
            logger.error('请求数据未解析到数据,丢弃数据。similar-44')
            return

        dyz = parse("$..subscriberCountText.accessibility.accessibilityData.label").find(data)[0].value
        dyz = re.findall(r'(\d.+?)位订阅者', dyz)
        author_id = [item.value for item in
                     parse('$..title.runs[*].navigationEndpoint.commandMetadata.webCommandMetadata.url').find(data)]
        if dyz and eval(dyz[0].replace('万', ' * 10000')) > 10000 and author_id:
            await self.save2('author', author_id[0])
            logger.info(f"author{author_id[0]} 已存储")

        token = await self.parse(data)
        while True:
            if not token:
                return
            self.page += 1
            if self.page - self.max_page != 0:
                logger.info(f"正在解析 {self.page} 页")
                data = await self.next_similar(token)
                token = await self.parse(data, type=1)
            else:
                return

    async def save(self, data: list):
        """保存id"""
        sql = 'insert into url(url) values (%s)'
        for item in data:
            if await self.mysql_db.insert_url(sql=sql, data=item):
                logger.info(f'存储成功{item}')
                await self.redis_db.lpush('author_id', item)

    async def save2(self, type: str, name: str):
        """
        用户id，通过来自那个初始化的，这样就能保证分类，不同分类有相同的用户
        视频id，
        :param type: watch_id, author_id
        :param key: 对应添加的key
        :param value: 添加的值
        :return:
        """
        value = json.dumps({'name': name, "source": self.source})
        if type == 'watch':
            # 视频
            data = await self.redis_db.sadd(key=self.source + "-w", value=value)
            if data:
                await self.redis_db.lpush(key=self.watch_id_set, value=value)
                logger.info(f'已存储watch_id:{name}')

        if type == 'author':
            # 用户
            data = await self.redis_db.sadd(key=self.source + "-a", value=value)
            if data:
                await self.redis_db.lpush(key='author_id', value=value)
                logger.info(f'已存储用户:{name}')

    async def parse(self, data: dict, type: int = 0):
        """
        :param data:
        :return:
        data 给author类
        """
        if type == 0:
            jsonpath_expr = parse('$.contents.twoColumnWatchNextResults.secondaryResults.secondaryResults.results')
        else:
            jsonpath_expr = parse('$.onResponseReceivedEndpoints[*].appendContinuationItemsAction.continuationItems')
        result = jsonpath_expr.find(data)[0].value
        for item in result:
            if "compactVideoRenderer" not in item.keys():
                continue
            watch_id = item.get('compactVideoRenderer').get('videoId')
            # author_id = parse('$.compactVideoRenderer.longBylineText..url').find(item)[0].value
            try:
                await self.save2('watch', watch_id)
                # await self.save2('author', author_id)
            except Exception as e:
                logger.info('存储reids出错')
                continue
        # 解析token
        jsonpath_expr = parse('$..button.buttonRenderer.command.continuationCommand.token')
        tokens = {match.value for match in jsonpath_expr.find(data)}
        if not tokens:
            logger.info('没有tokens')
            return
        return tokens.pop()

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
        response = await self.client.post(url=url, headers=await self.get_headers(), data=payload)
        return json.loads(response)

    async def back_fill(self, watch_id: str) -> None:
        logger.error(f'请求失败:-----> watch_id:{watch_id},执行回填')
        re_try = 0
        while re_try < 3:
            try:
                await self.redis_db.lpush(self.watch_id_set, watch_id)
                logger.error(f'回填成功:-----> watch_id:{watch_id}')
                return
            except Exception:
                re_try += 1
                logger.error(f'回填失败:-----> watch_id:{watch_id},重试次数：{3 - re_try}')

    async def run(self, watch_id_set: str = "mm"):
        await self.redis_db.init()
        await self.mysql_db.init_pool()
        await self.client.init()

        self.watch_id_set = watch_id_set

        while True:
            temp = await self.redis_db.rpop(self.watch_id_set)
            if not temp:
                logger.info(f'{self.source} 数据全部采集完成')
                logger.info('相似视频watch_id没有，休息中')
                try:
                    await self.redis_db.delete(self.source + "-a")
                    await self.redis_db.delete(self.source + "-w")
                except:
                    pass
                await asyncio.sleep(3)
                continue

            try:
                temp_json = json.loads(temp)
            except Exception as e:
                logger.error(f"数据格式不是json格式，数据丢弃{temp}")
                continue
            watch_id, self.source = temp_json['name'], temp_json['source']
            try:
                self.page = 0
                logger.info(f'开始获取watch_id:{watch_id}')
                await self.get_watch(watch_id)
            except Exception as e:
                logger.error(f'视频获取错误。丢弃{watch_id}')

                # await self.back_fill(watch_id=temp)


def run_similar_instance(instance: Similar, watch_id_set: str):
    asyncio.run(instance.run(watch_id_set))


if __name__ == '__main__':
    start = time.time()
    watch_id_set = "赚钱"
    max_page = 0

    # 创建 Similar 实例列表
    similar_instances = [Similar(max_page=max_page) for _ in range(5)]  # 假设创建5个实例

    # 使用 ThreadPoolExecutor 进行多线程处理
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_similar_instance, instance, watch_id_set) for instance in similar_instances]

    for future in as_completed(futures):
        try:
            future.result()  # 获取线程结果，触发异常处理
        except Exception as e:
            logger.error(f"线程执行出错: {e}")
    print(f"总执行时间: {time.time() - start} 秒")
