import asyncio

import aiofiles
import aiohttp
import redis
import yaml
from fake_useragent import UserAgent
from loguru import logger

ua = UserAgent()


async def get_config() -> dict:
    async with aiofiles.open('config.yaml', 'r') as f:
        data = yaml.safe_load(await f.read())
    return data


class RedisConnectionPool:
    def __init__(self, host='localhost', port=6379, db=0, max_connections=10):
        self.pool = redis.ConnectionPool(host=host, port=port, db=db, max_connections=max_connections)
        self.client = redis.Redis(connection_pool=self.pool)

    async def get_client(self):
        return self.client


def get_redis_client():
    redis_client = redis.Redis(
        host='127.0.0.1',
        port=6379,
        password='123456',
        db=11,
    )
    return redis_client


async def get_proxy():
    return {
        'http': "http://127.0.0.1:7890",
        'https': "http://127.0.0.1:7890"
    }


class AsyncHttpClient:
    def __init__(self):
        self.session = None

    async def init(self):
        self.session = aiohttp.ClientSession()
        logger.info("HTTP client session initialized")

    async def close(self):
        if self.session:
            await self.session.close()
            logger.info("HTTP client session closed")

    async def get(self, url, headers=None, **kwargs) -> str:
        try:
            proxies = await get_proxy()
            proxy = proxies.get('http') if url.startswith('http://') else proxies.get('https')
            async with self.session.get(url, headers=headers, proxy=proxy, **kwargs) as response:
                if response.status == 200:
                    text = await response.text()
                    return text
                else:
                    logger.error(f"Failed to fetch URL: {url}, Status Code: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Exception during GET request to {url}: {e}")
            return None

    async def post(self, url, data=None, headers=None, **kwargs):
        try:
            proxies = await get_proxy()
            proxy = proxies.get('http') if url.startswith('http://') else proxies.get('https')
            async with self.session.post(url, data=data, headers=headers, proxy=proxy, **kwargs) as response:
                if response.status == 200:
                    text = await response.text()
                    return text
                else:
                    text = await response.text()
                    logger.error(f"Failed to post to URL: {url}, Status Code: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Exception during POST request to {url}: {e}")
            return None


# 示例使用
async def main():
    client = AsyncHttpClient()
    await client.init()

    url = "https://www.baidu.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # 执行 GET 请求
    response = await client.get(url, headers=headers)
    print(f"GET response: {response}")

    # 执行 POST 请求
    # data = {"title": "foo", "body": "bar", "userId": 1}
    # response = await client.post(url, data=data, headers=headers)
    # print(f"POST response: {response}")

    await client.close()


# 运行主函数

# # 使用示例
# if __name__ == "__main__":
#     requester = RequestWithRetry(retries=3, backoff_factor=2)
#     try:
#         response = requester.get('https://httpbin.org/status/500')
#         print(response.status_code)
#     except requests.exceptions.RequestException as e:
#         print(f"Request failed: {e}")


if __name__ == '__main__':
    # async def main():
    #     await get_config()
    # asyncio.run(main())
    asyncio.run(main())
