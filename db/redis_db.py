import asyncio
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
    
    async def lrange(self, key, start=0, stop=-1):
        return await self.redis.lrange(key, start, stop)
    
    async def llen(self, key):
        return await self.redis.llen(key)


# 示例使用
async def main():
    redis_db = RedisDb()
    await redis_db.init()
    
    # await redis_db.lpush('mylist', 'value1')
    # await redis_db.lpush('mylist', 'value2')
    
    length = await redis_db.llen('mylist')
    print(f'List length: {length}')
    
    values = await redis_db.lrange('mylist', 0, -1)
    print(f'List values: {values}')
    
    value = await redis_db.rpop('mylist')
    print(f'Popped value: {value}')
    
    await redis_db.close()


# 运行主函数
asyncio.run(main())
