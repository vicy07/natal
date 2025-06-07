FROM python:3.11-slim

# Установка системных зависимостей для сборки swisseph и matplotlib
RUN apt-get update && apt-get install -y \
    build-essential \
    libopenblas-dev \
    libfreetype6-dev \
    libpng-dev \
    libgeos-dev \
    libatlas-base-dev \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходников приложения
COPY main.py .

# Порт
EXPOSE 8000

# Старт
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
