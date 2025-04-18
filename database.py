import asyncpg
from config import DB_CONFIG

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(**DB_CONFIG)

    async def create_tables(self):
        query = """
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            full_name TEXT NOT NULL,
            birth_date DATE NOT NULL,
            phone TEXT NOT NULL
        );
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query)

    async def add_user(self, full_name: str, birth_date: 'datetime.date', phone: str):
        query = """
        INSERT INTO users(full_name, birth_date, phone)
        VALUES($1, $2, $3)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, full_name, birth_date, phone)
