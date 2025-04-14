import asyncio
import os

import asyncpg
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DB_CONFIG = {
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "123"),
    "host": os.getenv("POSTGRES_HOST", "db"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "postgres"),
}

CREATE_USERS_TABLE_SQL = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('employee', 'moderator')) DEFAULT 'employee'
);
"""

CREATE_PVZ_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS PVZ_table (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    registration_date TIMESTAMPTZ DEFAULT now(),
    city TEXT NOT NULL CHECK (city IN ('Москва', 'Санкт-Петербург', 'Казань'))
);
"""

CREATE_RECEPTION_SQL = """
CREATE TABLE IF NOT EXISTS receptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    datetime TIMESTAMPTZ DEFAULT now(),
    pvzId UUID NOT NULL REFERENCES PVZ_table(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('in_progress', 'close')) DEFAULT 'in_progress'
);
"""

CREATE_PRODUCTS_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    datetime TIMESTAMPTZ DEFAULT now(),
    receptionId UUID NOT NULL REFERENCES receptions(id) ON DELETE CASCADE,
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
        await conn.execute(CREATE_PRODUCTS_SQL)

        print("Готово! Таблицы созданы.")
        await conn.close()
    except Exception as e:
        print("Ошибка при создании базы:", e)
