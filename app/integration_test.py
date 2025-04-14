import requests

def print_error(response, context=""):
    print(f"❌ Ошибка на этапе {context}: {response.status_code}")
    print(response.text)

print("Итоги интеграционного тестирования")
# 1. Авторизация модератора
url_login = "http://127.0.0.1:8000/dummyLogin"
data_login = {"role": "moderator"}
headers_login = {"Content-Type": "application/json"}

response_login = requests.post(url_login, json=data_login, headers=headers_login)
if response_login.status_code != 200:
    print_error(response_login, "авторизации модератора")
else:
    #print("✅ Токен модератора получен.")
    access_token_moderator = response_login.json().get("access_token")

    # 2. Создание ПВЗ
    url_pvz = "http://127.0.0.1:8000/pvz"
    data_pvz = {"city": "Москва"}
    headers_pvz = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token_moderator}"
    }

    response_pvz = requests.post(url_pvz, json=data_pvz, headers=headers_pvz)
    if response_pvz.status_code != 201:
        print_error(response_pvz, "создания ПВЗ")
    else:
        print("✅ ПВЗ успешно создан.")

        # 3. Авторизация сотрудника
        data_login_employee = {"role": "employee"}
        headers_login_employee = {"Content-Type": "application/json"}
        response_login_employee = requests.post(url_login, json=data_login_employee, headers=headers_login_employee)

        if response_login_employee.status_code != 200:
            print_error(response_login_employee, "авторизации сотрудника")
        else:
            #print("✅ Токен сотрудника получен.")
            access_token_employee = response_login_employee.json().get("access_token")

            # 4. Получение id ПВЗ
            url_pvz_get = "http://127.0.0.1:8000/pvz?startDate=&endDate=&limit=1&page=2"
            headers_pvz_get = {
                "Authorization": f"Bearer {access_token_moderator}",
                "Content-Type": "application/json"
            }

            response_pvz_get = requests.get(url_pvz_get, headers=headers_pvz_get)
            if response_pvz_get.status_code != 200:
                print_error(response_pvz_get, "получения данных о ПВЗ")
            else:
                response_data_pvz_get = response_pvz_get.json()
                pvz_id = response_data_pvz_get[0].get("pvz", {}).get("id")
                if not pvz_id:
                    print("❌ Не удалось получить ID ПВЗ.")
                else:
                    #print(f"✅ Получен ID ПВЗ: {pvz_id}")

                    # 5. Создание приёмки
                    url_receptions = "http://127.0.0.1:8000/receptions"
                    data_receptions = {"pvzId": pvz_id}
                    headers_receptions = {
                        "Authorization": f"Bearer {access_token_employee}",
                        "Content-Type": "application/json"
                    }

                    response_receptions = requests.post(url_receptions, json=data_receptions, headers=headers_receptions)
                    if response_receptions.status_code != 201:
                        print_error(response_receptions, "создания приёмки")
                    else:
                        print("✅ Приемка успешно создана.")

                        # 6. Создание 50 товаров
                        url_products = "http://127.0.0.1:8000/products"
                        headers_products = {
                            "Authorization": f"Bearer {access_token_employee}",
                            "Content-Type": "application/json"
                        }

                        success_count = 0
                        for _ in range(50):
                            data_products = {
                                "type": "электроника",
                                "pvzId": pvz_id
                            }

                            response = requests.post(url_products, json=data_products, headers=headers_products)
                            if response.status_code == 201:
                                success_count += 1
                            else:
                                break  

                        if success_count == 50:
                            print("✅ Все 50 товаров успешно созданы.")
                            
                            # 7. Закрытие приёмки
                            url_close_reception = f"http://127.0.0.1:8000/pvz/{pvz_id}/close_last_reception"
                            headers_close = {
                                "Authorization": f"Bearer {access_token_employee}",
                                "Content-Type": "application/json"
                            }

                            response_close = requests.post(url_close_reception, headers=headers_close)
                            if response_close.status_code == 200:
                                print("✅ Приемка успешно закрыта.")
                            else:
                                print_error(response_close, "закрытия приёмки")
                        else:
                            print(f"❌ Создано только {success_count} товаров из 50.")
