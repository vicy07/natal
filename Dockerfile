FROM python:3.11-slim

# Установка всех системных зависимостей
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
    gfortran \
    libopenblas-dev \
    libgeos-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Настройка локали
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Создание пользователя и установка рабочей директории
WORKDIR /app
RUN useradd -m appuser && chown -R appuser /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

USER appuser

EXPOSE 8000

# ⛳️ Ключевое изменение: убираем app. перед main
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
