echo "Ожидаем 10 секунд, пока база данных запустится..."
sleep 10


python init_db.py



uvicorn main:app --host 0.0.0.0 --port 8000 --workers 6
