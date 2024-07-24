import asyncio
import aiomysql
from tools import get_config


class AsyncMySQLManager:
    def __init__(self, concurrency=10):
        self.mysql_config = get_config().get('mysql')
        self.concurrency = concurrency
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
                    await cur.execute("INSERT INTO urls (url) VALUES (%s)",
                                      (url,))
                    await conn.commit()
                except aiomysql.IntegrityError as e:
                    print(f"IntegrityError: {e}")
    
    async def process_urls(self, urls):
        semaphore = asyncio.Semaphore(self.concurrency)
        
        async def sem_insert_url(url):
            async with semaphore:
                await self.insert_url(url)
        
        tasks = [sem_insert_url(url) for url in urls]
        await asyncio.gather(*tasks)


# 使用示例
if __name__ == '__main__':
    async with AsyncMySQLManager() as db_manager:
        tasks = db_manager.process_url("url")
        # tasks = [url_processor.process_url(url) for url in urls]
        await asyncio.gather(*tasks)
    

