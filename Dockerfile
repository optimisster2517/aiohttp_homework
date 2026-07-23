FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY models.py .
COPY aiohttp_app.py .
COPY aiohttp_app_with_auth.py .

# Открытие порта
EXPOSE 8080

# Запуск приложения (по умолчанию базовая версия)
CMD ["python", "aiohttp_app.py"]
