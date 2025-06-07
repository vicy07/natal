FROM python:3.11-slim

# Установка необходимых системных библиотек
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libopenblas-dev \
    libfreetype6-dev \
    libpng-dev \
    libgeos-dev \
    curl \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Настройка UTF-8
RUN apt-get install -y locales && \
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Создание рабочего каталога
WORKDIR /app

# Обновление pip и установка зависимостей
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir --use-pep517 swisseph \
 && pip install --no-cache-dir -r requirements.txt

# Копирование исходников
COPY . .

# Экспонирование порта
EXPOSE 8000

# Запуск FastAPI через uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
