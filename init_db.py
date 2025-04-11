from passlib.context import CryptContext
import asyncio
import asyncpg

# Инициализация CryptContext для хеширования
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройки подключения к базе данных
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

async def create_user(email: str, password: str, role: str = 'employee'):
    try:
        # Подключение к базе данных
        conn = await asyncpg.connect(**DB_CONFIG)

        # Вставка нового пользователя в таблицу
        await conn.execute("""
            INSERT INTO users (email, password, role)
            VALUES ($1, $2, $3)
        """, email, password, role)

        print(f"Пользователь с email {email} добавлен.")
        await conn.close()
    except Exception as e:
        print("Ошибка при создании пользователя:", e)


if __name__ == "__main__":
    # Создаем таблицу и добавляем пользователя без поля name
    asyncio.run(create_db())
    asyncio.run(create_user("johndoe@example.com", "password123"))
