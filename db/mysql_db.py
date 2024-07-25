import asyncio
import aiomysql
from tools import get_config
from loguru import logger


class AsyncMySQLManager:
    def __init__(self, concurrency=10):
        self.mysql_config = None
        self.concurrency = concurrency
        self.db_pool = None
    
    async def init_pool(self):
        config = await get_config()
        self.mysql_config = config.get('mysql')
        print(self.mysql_config)
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
    
    async def insert_url(self, sql: str, data: list):
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(sql, data)
                    await conn.commit()
                    return True
                except aiomysql.IntegrityError as e:
                    logger.info(f'数据已存在,{e}')
                    return False
                except Exception as e:
                    logger.info(f'存储出错--->{e}')
                    return
    
    async def process_url(self, sql: str, data: list):
        return await self.insert_url(sql=sql, data=data)


async def main(url):
    sql_manage = AsyncMySQLManager()
    await sql_manage.init_pool()
    result = await sql_manage.insert_url('insert into title(name, `title`) values (%s, %s)', data=["fsfsfs", 'ddd'])
    print(result)


if __name__ == '__main__':
    asyncio.run(main(["fsfsfs", 'ddd']))
