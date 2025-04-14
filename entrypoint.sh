echo "Ожидаем 6 секунд, пока база данных запустится..."
sleep 6

python app/init_db.py
python app/unit_tests.py


uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 6 & 
SERVER_PID=$!


echo "Ожидание запуска сервера..."
until curl -s http://localhost:8000/register > /dev/null; do
  sleep 1
done
echo "Сервер запущен!"


python app/integration_test.py


wait $SERVER_PID
