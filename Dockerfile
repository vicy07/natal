FROM python:3.11-slim

# Install essential build tools and libraries for most pip packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    pkg-config \
    wget \
    curl \
    git \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    libsqlite3-dev \
    libjpeg-dev \
    libfreetype6-dev \
    locales \
    tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY main.py .

# Экспонируем порт
EXPOSE 8000

# Запуск сервиса
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
