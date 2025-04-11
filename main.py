from fastapi import *
import asyncpg
from asyncpg.pool import Pool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from starlette.status import HTTP_400_BAD_REQUEST
from init_db import DB_CONFIG
from schemas import *


app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"description": "Неверный запрос"}),
    )


# Глобальный пул подключений
db_pool: Pool = None




async def insert_user(email: str, password: str, role: str):
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (email, password, role)
                VALUES ($1, $2, $3)
            """, email, password, role)
    except asyncpg.exceptions.UniqueViolationError:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    await insert_user(user.email, user.password, user.role)
    return {"description": "Пользователь создан"}


@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(**DB_CONFIG)


@app.on_event("shutdown")
async def shutdown():
    await db_pool.close()
