echo "Ожидаем 6 секунд, пока база данных запустится..."
sleep 6

python init_db.py
python unit_tests.py

# Запускаем сервер в фоне
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 6 & 
SERVER_PID=$!

# Ожидаем, пока сервер начнёт принимать подключения
echo "Ожидание запуска сервера..."
until curl -s http://localhost:8000/register > /dev/null; do
  sleep 1
done
echo "Сервер запущен!"

# Запускаем интеграционные тесты
python integration_test.py

# Не убиваем сервер, оставляем его работать
wait $SERVER_PID
