import asyncio

import redis
import requests
from retrying import retry
import yaml
import aiofiles


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


async def get_proxy():
    proxy = {
        'http': "http://127.0.0.1:7890",
        'https': "https://127.0.0.1:7890"
    }
    return proxy


class RequestWithRetry:
    def __init__(self, retries=3, backoff_factor=1, status_forcelist=(500, 502, 504)):
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.status_forcelist = status_forcelist
    
    @retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000)
    def _send_request(self, method, url, **kwargs):
        response = requests.request(method, url, **kwargs)
        if response.status_code in self.status_forcelist:
            response.raise_for_status()
        return response
    
    def get(self, url, **kwargs):
        return self._send_request('GET', url, **kwargs)
    
    def post(self, url, **kwargs):
        return self._send_request('POST', url, **kwargs)
    
    def put(self, url, **kwargs):
        return self._send_request('PUT', url, **kwargs)
    
    def delete(self, url, **kwargs):
        return self._send_request('DELETE', url, **kwargs)


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

    get_redis_client()