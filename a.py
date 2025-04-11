import asyncio
import asyncpg
from passlib.context import CryptContext

# Настройка контекста для работы с bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Конфигурация подключения к базе
DB_CONFIG = {
    "user": "postgres",
    "password": "123",
    "host": "localhost",
    "port": 5432,
    "database": "PVZ",
}

# Функция для сравнения пароля пользователя с хешем из базы
async def verify_user_password(user_id: int, input_password: str):
    try:
        conn = await asyncpg.connect(**DB_CONFIG)

        row = await conn.fetchrow("SELECT password FROM users WHERE id = $1", user_id)

        if not row:
            print("Пользователь не найден.")
            return

        hashed_password = row["password"]

        if pwd_context.verify(input_password, hashed_password):
            print("Угадал")
        else:
            print("Не угадал")

        await conn.close()

    except Exception as e:
        print("Ошибка при проверке пароля:", e)

# Пример запуска
if __name__ == "__main__":
    user_input_password = input("Введите пароль: ")
    asyncio.run(verify_user_password(1, user_input_password))
