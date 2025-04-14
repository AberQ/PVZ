echo "Ожидаем 6 секунд, пока база данных запустится..."
sleep 6


python init_db.py




python unit_tests.py



uvicorn main:app --host 0.0.0.0 --port 8000 --workers 6

