from passlib.context import CryptContext
import asyncio
import asyncpg
import os
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DB_CONFIG = {
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "123"),
    "host": os.getenv("POSTGRES_HOST", "db"), 
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "postgres"),
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

CREATE_RECEPTION_SQL = """
CREATE TABLE IF NOT EXISTS receptions (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMPTZ DEFAULT now(),
    pvzId INTEGER NOT NULL REFERENCES PVZ_table(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('in_progress', 'close')) DEFAULT 'in_progress'
);
"""

CREATE_Products_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMPTZ DEFAULT now(),
    receptionId INTEGER NOT NULL REFERENCES receptions(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('электроника', 'одежда', 'обувь'))
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

        print("Создание таблицы receptions...")
        await conn.execute(CREATE_RECEPTION_SQL)

        print("Создание таблицы products...")
        await conn.execute(CREATE_Products_SQL)

        print("Готово! Таблицы созданы.")
        await conn.close()
    except Exception as e:
        print("Ошибка при создании базы:", e)

async def create_user(email: str, password: str, role: str = 'employee'):
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        hashed_password = pwd_context.hash(password)

        await conn.execute("""
            INSERT INTO users (email, password, role)
            VALUES ($1, $2, $3)
        """, email, hashed_password, role)

        print(f"Пользователь с email {email} добавлен.")
        await conn.close()
    except Exception as e:
        print("Ошибка при создании пользователя:", e)

async def create_test_pvz(city: str = "Москва") -> int:
    try:
        conn = await asyncpg.connect(**DB_CONFIG)

        result = await conn.fetchrow("""
            INSERT INTO PVZ_table (city) VALUES ($1)
            RETURNING id
        """, city)

        pvz_id = result['id']
        print(f"Тестовая запись ПВЗ с городом '{city}' добавлена, ID: {pvz_id}.")
        await conn.close()
        return pvz_id
    except Exception as e:
        print("Ошибка при добавлении тестового ПВЗ:", e)
        return -1

async def create_goods_reception(pvz_id: int, status: str = "in_progress") -> int:
    try:
        conn = await asyncpg.connect(**DB_CONFIG)

        result = await conn.fetchrow("""
            INSERT INTO receptions (pvzId, status)
            VALUES ($1, $2)
            RETURNING id
        """, pvz_id, status)

        reception_id = result["id"]
        print(f"Приёмка товара создана, ID: {reception_id}")
        await conn.close()
        return reception_id
    except Exception as e:
        print("Ошибка при создании приёмки:", e)
        return -1

async def create_products(reception_id: int, item_type: str = "электроника"):
    try:
        conn = await asyncpg.connect(**DB_CONFIG)

        await conn.execute("""
            INSERT INTO products (receptionId, type)
            VALUES ($1, $2)
        """, reception_id, item_type)

        print(f"Товар типа '{item_type}' добавлен к приёмке ID {reception_id}.")
        await conn.close()
    except Exception as e:
        print("Ошибка при добавлении товара:", e)

# Пример запуска
if __name__ == "__main__":
    async def main():
        await create_db()
        await create_user("johndoe@example.com", "password123")

        pvz_id = await create_test_pvz("Москва")
        if pvz_id != -1:
            reception_id = await create_goods_reception(pvz_id)
            if reception_id != -1:
                await create_products(reception_id, "электроника")
                await create_products(reception_id, "одежда")

    asyncio.run(main())
