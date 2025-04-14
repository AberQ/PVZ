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
from typing import List
from uuid import UUID
from fastapi import Body

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
        raise HTTPException(status_code=400, detail="Неверный запрос")

    access_token = create_access_token(data={"sub": user.role})
    return {"description": "Успешная авторизация", "access_token": access_token}


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

# Получение всех ПВЗ
from fastapi import Query

# Получение ПВЗ с фильтрацией по дате приемки и пагинацией
async def get_filtered_pvz(start_date: str = None, end_date: str = None, page: int = 1, limit: int = 10):
    try:
        async with db_pool.acquire() as conn:
            # Строим базовый SQL запрос
            base_query = """
                SELECT * FROM PVZ_table
            """
            filters = []
            if start_date:
                filters.append(f"registration_date >= '{start_date}'")
            if end_date:
                filters.append(f"registration_date <= '{end_date}'")

            # Применяем фильтры, если они есть
            if filters:
                base_query += " WHERE " + " AND ".join(filters)

            # Добавляем пагинацию
            base_query += f" ORDER BY registration_date LIMIT {limit} OFFSET {(page - 1) * limit}"
            
            # Получаем данные
            rows = await conn.fetch(base_query)
            
            # Формируем результат
            pvz_list = []
            for row in rows:
                # Для каждого ПВЗ, получаем связанные приемки
                receptions = await conn.fetch("""
                    SELECT * FROM receptions WHERE pvzId = $1
                """, row["id"])
                
                # Для каждой приемки, получаем товары
                reception_details = []
                for reception in receptions:
                    products = await conn.fetch("""
                        SELECT * FROM products WHERE receptionId = $1
                    """, reception["id"])
                    reception_details.append({
                        "reception": dict(reception),
                        "products": [dict(product) for product in products]
                    })
                
                pvz_list.append({
                    "pvz": dict(row),
                    "receptions": reception_details
                })

            return pvz_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {str(e)}")


# Маршрут для получения всех ПВЗ
@app.get("/pvz", response_model=List[dict])
async def list_pvz(
    startDate: str = Query(None, description="Начальная дата диапазона"),
    endDate: str = Query(None, description="Конечная дата диапазона"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(10, ge=1, le=30, description="Количество элементов на странице"),
    role: str = Depends(get_current_role)
):
    if role not in ["employee", "moderator"]:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    
    pvz_list = await get_filtered_pvz(start_date=startDate, end_date=endDate, page=page, limit=limit)
    return pvz_list



async def has_open_reception(pvz_id: int) -> bool:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id FROM receptions
            WHERE pvzId = $1 AND status = 'in_progress'
        """, pvz_id)
        return row is not None



async def create_reception(pvz_id: int) -> dict:
    new_id = uuid.uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO receptions (id, pvzId, datetime, status)
            VALUES ($1, $2, NOW(), 'in_progress')
        """, new_id, pvz_id)
        return await conn.fetchrow("""
            SELECT * FROM receptions WHERE id = $1
        """, new_id)



async def pvz_exists(pvz_id: int) -> bool:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM PVZ_table WHERE id = $1", pvz_id)
        return row is not None


@app.post("/receptions", response_model=Reception, status_code=201)
async def create_new_reception(data: ReceptionCreate, role: str = Depends(get_current_role)):
    if role != "employee":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    if not await pvz_exists(data.pvzId):
        raise HTTPException(status_code=400, detail="Неверный запрос или есть незакрытая приемка")

    if await has_open_reception(data.pvzId):
        raise HTTPException(status_code=400, detail="Неверный запрос или есть незакрытая приемка")

    reception = await create_reception(data.pvzId)
    return JSONResponse(
        status_code=201,
        content={
            "description": "Приемка создана"
        }
    )




async def get_active_reception_id(pvz_id: UUID) -> UUID:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id FROM receptions
            WHERE pvzId = $1 AND status = 'in_progress'
            ORDER BY datetime DESC
            LIMIT 1
        """, pvz_id)
        return row["id"] if row else None




async def insert_product(product_type: str, reception_id: UUID):
    product_id = uuid.uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO products (id, type, receptionId)
            VALUES ($1, $2, $3)
        """, product_id, product_type, reception_id)





@app.post("/products", status_code=201)
async def add_product(
    data: ProductCreate = Body(...),
    role: str = Depends(get_current_role)
):
    if role != "employee":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    reception_id = await get_active_reception_id(data.pvzId)
    if not reception_id:
        raise HTTPException(status_code=400, detail="Неверный запрос или нет активной приемки")

    await insert_product(data.type, reception_id)

    return {"description": "Товар добавлен"}






async def get_active_reception_id(pvz_id: UUID) -> UUID:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id FROM receptions
            WHERE pvzId = $1 AND status = 'in_progress'
            ORDER BY datetime DESC
            LIMIT 1
        """, pvz_id)
        return row["id"] if row else None

# Закрытие последней активной приемки
async def close_last_reception(pvz_id: UUID):
    active_reception_id = await get_active_reception_id(pvz_id)
    if not active_reception_id:
        raise HTTPException(status_code=400, detail="Неверный запрос или приемка уже закрыта")

    async with db_pool.acquire() as conn:
        
        await conn.execute("""
            UPDATE receptions SET status = 'close' WHERE id = $1
        """, active_reception_id)

        # Получаем обновленную приемку
        reception = await conn.fetchrow("""
            SELECT * FROM receptions WHERE id = $1
        """, active_reception_id)
        return dict(reception)


@app.post("/pvz/{pvzId}/close_last_reception", status_code=200)
async def close_last_reception_endpoint(pvzId: UUID, role: str = Depends(get_current_role)):
    if role != "employee":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        reception = await close_last_reception(pvzId)
        return JSONResponse(content={"description": "Приемка закрыта"})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")





@app.post("/pvz/{pvz_id}/delete_last_product", status_code=200, summary="Удаление последнего добавленного товара из текущей приемки (LIFO, только для сотрудников ПВЗ)")
async def delete_last_product(pvz_id: UUID, role: str = Depends(get_current_role)):
    if role != "employee":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        # Найти приёмку со статусом in_progress
        reception = await conn.fetchrow("""
            SELECT id FROM receptions
            WHERE pvzId = $1 AND status = 'in_progress'
            ORDER BY datetime DESC
            LIMIT 1
        """, str(pvz_id))

        if not reception:
            raise HTTPException(status_code=400, detail="Неверный запрос, нет активной приемки или нет товаров для удаления")

        reception_id = reception["id"]

        # Найти последний добавленный товар (LIFO)
        product = await conn.fetchrow("""
            SELECT id FROM products
            WHERE receptionId = $1
            ORDER BY datetime DESC
            LIMIT 1
        """, str(reception_id))

        if not product:
            raise HTTPException(status_code=400, detail="Неверный запрос, нет активной приемки или нет товаров для удаления")

        # Удалить товар
        await conn.execute("DELETE FROM products WHERE id = $1", product["id"])
        return {"description": "Товар удален"}



    finally:
        await conn.close()


# Подключение к базе при старте
@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(**DB_CONFIG)






# Закрытие пула при завершении
@app.on_event("shutdown")
async def shutdown():
    await db_pool.close()

