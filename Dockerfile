FROM python:3.11-slim

# Установка всех нужных системных библиотек и локали
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libopenblas-dev \
    libfreetype6-dev \
    libpng-dev \
    libgeos-dev \
    curl \
    git \
    locales \
 && sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen \
 && locale-gen \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Рабочая папка
WORKDIR /app

# Установка зависимостей (включая swisseph)
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir --use-pep517 swisseph \
 && pip install --no-cache-dir -r requirements.txt

# Копируем исходники
COPY . .

# Порт
EXPOSE 8000

# Запуск
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
