import asyncio
import aiomysql
from tools import get_config


class AsyncMySQLManager:
    def __init__(self, concurrency=10):
        self.mysql_config = get_config().get('mysql')
        self.concurrency = concurrency
        self.db_pool = None
    
    async def init_pool(self):
        self.db_pool = await aiomysql.create_pool(
            host=self.mysql_config['host'],
            port=self.mysql_config['port'],
            user=self.mysql_config['user'],
            password=self.mysql_config['password'],
            db=self.mysql_config['db'],
            minsize=self.mysql_config.get('minsize', 1),
            maxsize=self.mysql_config.get('maxsize', 10)
        )
    
    async def close_pool(self):
        if self.db_pool:
            self.db_pool.close()
            await self.db_pool.wait_closed()
    
    async def insert_url(self, url):
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute("INSERT INTO urls (url) VALUES (%s)", (url,))
                    await conn.commit()
                except aiomysql.IntegrityError as e:
                    print(f"IntegrityError: {e}")
    
    async def process_url(self, url):
        await self.insert_url(url)
    
    async def __aenter__(self):
        await self.init_pool()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.close_pool()


async def main():
    url = "http://example.com/1"

    async with AsyncMySQLManager() as db_manager:
        await db_manager.process_url(url)

if __name__ == '__main__':
    asyncio.run(main())