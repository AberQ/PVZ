from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg

app = FastAPI()

# Модель пользователя
class UserCreate(BaseModel):
    name: str
    email: str

# Инициализация подключения
@app.on_event("startup")
async def startup():
    app.state.db = await asyncpg.connect(
        user="your_user",
        password="your_password",
        database="your_database",
        host="localhost",
        port=5432
    )

@app.on_event("shutdown")
async def shutdown():
    await app.state.db.close()


# Получение списка пользователей
@app.get("/users")
async def get_users():
    rows = await app.state.db.fetch("SELECT id, name, email FROM users")
    return [dict(row) for row in rows]


# Добавление пользователя
@app.post("/users")
async def create_user(user: UserCreate):
    try:
        await app.state.db.execute(
            "INSERT INTO users (name, email) VALUES ($1, $2)",
            user.name,
            user.email
        )
        return {"message": "User created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
