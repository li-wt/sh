import asyncio
import json

from redis.asyncio import Redis

from tools import get_config


class RedisDb:
    def __init__(self):
        self.redis_config = None
        self.redis = None
    
    async def init(self):
        """
        创建连接
        """
        config = await get_config()
        self.redis_config = config.get('redis')
        
        self.redis = Redis(
            host=self.redis_config.get('host'),
            port=self.redis_config.get('port'),
            password=self.redis_config.get('password'),
            db=self.redis_config.get('db'),
            decode_responses=True
        )
    
    async def close(self):
        await self.redis.aclose()
    
    async def lpush(self, key, value):
        await self.redis.lpush(key, value)
    
    async def rpop(self, key):
        return await self.redis.rpop(key)
    
    async def sadd(self, key, value):
        return await self.redis.sadd(key, value)
    
    async def lrange(self, key, start=0, stop=-1):
        return await self.redis.lrange(key, start, stop)
    
    async def llen(self, key):
        return await self.redis.llen(key)
    
    async def delete(self, key):
        return await self.redis.delete(key)


# 示例使用

if __name__ == '__main__':
    async def main():
        redis_db = RedisDb()
        await redis_db.init()
        
        await redis_db.lpush("watch_id", json.dumps({'name': '8_aG6r_hR14', 'source': "test"}))
        await redis_db.close()
    
    
    asyncio.run(main())
