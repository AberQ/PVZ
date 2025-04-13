# Базовый образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Открываем порт (если FastAPI работает на 8000)
EXPOSE 8000

# Запуск FastAPI через uvicorn с 6 воркерами
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "6"]
