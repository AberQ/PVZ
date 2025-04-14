FROM python:3.11-slim


RUN apt-get update && apt-get install -y curl


WORKDIR /app


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


COPY . .

# Открываем порт (если FastAPI работает на 8000)
EXPOSE 8080


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "6"]
