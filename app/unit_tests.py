from init_db import *


print("UNIT-ТЕСТИРОВАНИЕ")
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

async def create_test_pvz(city: str = "Москва") -> str:
    try:
        conn = await asyncpg.connect(**DB_CONFIG)

        result = await conn.fetchrow("""
            INSERT INTO PVZ_table (city) VALUES ($1)
            RETURNING id
        """, city)

        pvz_id = str(result['id'])
        print(f"Тестовая запись ПВЗ с городом '{city}' добавлена, ID: {pvz_id}.")
        await conn.close()
        return pvz_id
    except Exception as e:
        print("Ошибка при добавлении тестового ПВЗ:", e)
        return ""

async def create_goods_reception(pvz_id: str, status: str = "in_progress") -> str:
    try:
        conn = await asyncpg.connect(**DB_CONFIG)

        result = await conn.fetchrow("""
            INSERT INTO receptions (pvzId, status)
            VALUES ($1, $2)
            RETURNING id
        """, pvz_id, status)

        reception_id = str(result["id"])
        print(f"Приёмка товара создана, ID: {reception_id}")
        await conn.close()
        return reception_id
    except Exception as e:
        print("Ошибка при создании приёмки:", e)
        return ""

async def create_products(reception_id: str, item_type: str = "электроника"):
    try:
        conn = await asyncpg.connect(**DB_CONFIG)

        result = await conn.fetchrow("""
            INSERT INTO products (receptionId, type)
            VALUES ($1, $2)
            RETURNING id
        """, reception_id, item_type)

        product_id = str(result['id'])
        print(f"Товар типа '{item_type}' добавлен к приёмке ID {reception_id}. ID товара: {product_id}")
        await conn.close()
        return product_id
    except Exception as e:
        print("Ошибка при добавлении товара:", e)
        return ""


async def delete_product(product_id: str):
    try:
        conn = await asyncpg.connect(**DB_CONFIG)


        await conn.execute("""
            DELETE FROM products
            WHERE id = $1
        """, product_id)

        print(f"Товар с ID {product_id} удалён.")
        await conn.close()
    except Exception as e:
        print("Ошибка при удалении товара:", e)


async def close_reception(reception_id: str):
    try:
        conn = await asyncpg.connect(**DB_CONFIG)


        await conn.execute("""
            UPDATE receptions
            SET status = 'close'
            WHERE id = $1
        """, reception_id)

        print(f"Приёмка с ID {reception_id} закрыта.")
        await conn.close()
    except Exception as e:
        print("Ошибка при закрытии приёмки:", e)

if __name__ == "__main__":
    async def main():
        await create_db()
        await create_user("johndoe@example.com", "password123")

  
        pvz_id = await create_test_pvz("Москва")
        if pvz_id:
            reception_id = await create_goods_reception(pvz_id, "in_progress")
            
            if reception_id:
                product_id_1 = await create_products(reception_id, "электроника")
                product_id_2 = await create_products(reception_id, "одежда")
                product_id_3 = await create_products(reception_id, "одежда")

                await delete_product(product_id_1)
                await delete_product(product_id_2)
  
                await close_reception(reception_id)

               

    asyncio.run(main())
