import asyncio
import asyncpg

DB_CONFIG = {
    "user": "postgres",
    "password": "123",
    "host": "localhost",
    "port": 5432,
    "database": "PVZ",
}

CREATE_USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);
"""

async def create_db():
    try:
        print("Подключение к базе данных...")
        conn = await asyncpg.connect(**DB_CONFIG)
        print("Создание таблицы users...")
        await conn.execute(CREATE_USERS_TABLE_SQL)
        print("Готово! Таблица создана.")
        await conn.close()
    except Exception as e:
        print("Ошибка при создании базы:", e)

if __name__ == "__main__":
    asyncio.run(create_db())
