# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Инициализируем БД (если нужно)
RUN python -c "from app import init_db; init_db()"

# Порт для Render
EXPOSE 5000

# Запуск (используем gunicorn для продакшена)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "app:app"]