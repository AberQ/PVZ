from passlib.context import CryptContext
import asyncio
import asyncpg

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('employee', 'moderator')) DEFAULT 'employee'
);
"""

CREATE_PVZ_TABLE_SQL = """
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS PVZ_table (
    id SERIAL PRIMARY KEY,
    registration_date TIMESTAMPTZ DEFAULT now(),
    city TEXT NOT NULL CHECK (city IN ('Москва', 'Санкт-Петербург', 'Казань'))
);
"""

async def create_db():
    try:
        print("Подключение к базе данных...")
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("Создание таблицы users...")
        await conn.execute(CREATE_USERS_TABLE_SQL)

        print("Создание таблицы PVZ_table...")
        await conn.execute(CREATE_PVZ_TABLE_SQL)

        print("Готово! Таблицы созданы.")
        await conn.close()
    except Exception as e:
        print("Ошибка при создании базы:", e)

async def create_user(email: str, password: str, role: str = 'employee'):
    try:
        conn = await asyncpg.connect(**DB_CONFIG)

        await conn.execute("""
            INSERT INTO users (email, password, role)
            VALUES ($1, $2, $3)
        """, email, password, role)

        print(f"Пользователь с email {email} добавлен.")
        await conn.close()
    except Exception as e:
        print("Ошибка при создании пользователя:", e)

async def create_test_pvz(city: str = "Москва"):
    try:
        conn = await asyncpg.connect(**DB_CONFIG)

        await conn.execute("""
            INSERT INTO PVZ_table (city) VALUES ($1)
        """, city)

        print(f"Тестовая запись ПВЗ с городом '{city}' добавлена.")
        await conn.close()
    except Exception as e:
        print("Ошибка при добавлении тестового ПВЗ:", e)

if __name__ == "__main__":
    asyncio.run(create_db())
    asyncio.run(create_user("johndoe@example.com", "password123"))
    asyncio.run(create_test_pvz())
