FROM python:3.11-slim

# Обновляем и устанавливаем все зависимости для сборки swisseph
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libopenblas-dev \
    libfreetype6-dev \
    libpng-dev \
    libgeos-dev \
    wget \
    git \
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
