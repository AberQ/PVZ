from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
import asyncpg
from asyncpg.pool import Pool
from starlette.status import HTTP_400_BAD_REQUEST
from init_db import DB_CONFIG
from schemas import *

app = FastAPI()

# JWT конфигурация
SECRET_KEY = "0tyfd1TNrniHOvE8KwmLjyDTQ1x025K6hkZVQfVwvSE"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"description": "Неверный запрос"}),
    )


# Глобальный пул подключений
db_pool: Pool = None


# Вставка пользователя в БД
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


# Регистрация пользователя
@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    await insert_user(user.email, user.password, user.role)
    return {"description": "Пользователь создан"}


# Создание JWT токена
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@app.post("/dummyLogin")
async def dummy_login(user: UserTypeRequest):
    if user.role not in ["employee", "moderator"]:
        raise HTTPException(status_code=400, detail="Неверный тип пользователя")

    access_token = create_access_token(data={"sub": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


# Получение роли из токена
async def get_current_role(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role: str = payload.get("sub")
        if role is None:
            raise HTTPException(status_code=401, detail="Недопустимый токен")
        return role
    except JWTError:
        raise HTTPException(status_code=401, detail="Не удалось проверить токен")


# Вставка ПВЗ
async def insert_pvz(city: str):
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("INSERT INTO PVZ_table (city) VALUES ($1)", city)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении ПВЗ: {str(e)}")


# Добавление нового ПВЗ (только для модераторов)
@app.post("/pvz", status_code=status.HTTP_201_CREATED)
async def create_pvz(pvz: PVZCreate, role: str = Depends(get_current_role)):
    if role != "moderator":
        raise HTTPException(status_code=403, detail="Доступ запрещён: требуется роль 'moderator'")
    await insert_pvz(pvz.city)
    return {"description": f"ПВЗ создан"}


# Подключение к базе при старте
@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(**DB_CONFIG)


# Закрытие пула при завершении
@app.on_event("shutdown")
async def shutdown():
    await db_pool.close()
