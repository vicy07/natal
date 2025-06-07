# Базовый образ
FROM python:3.11-slim

# Обновление системы и установка зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libopenblas-dev \
    libfreetype6-dev \
    libpng-dev \
    libgeos-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочего каталога
WORKDIR /app

# Копирование файлов
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Открытие порта
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
