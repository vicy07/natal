FROM python:3.11-slim

# Установка необходимых системных библиотек
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libopenblas-dev \
    libfreetype6-dev \
    libpng-dev \
    libgeos-dev \
    locales \
    curl \
    git \
 && sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen \
 && locale-gen \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV PYTHONUNBUFFERED=1

# Рабочая директория
WORKDIR /app

# Копирование файлов раньше — чтобы использовать кэш при повторной сборке
COPY . .

# Обновление pip и установка зависимостей
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir --use-pep517 swisseph \
 && pip install --no-cache-dir -r requirements.txt

# Экспонирование порта
EXPOSE 8000

# Запуск
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
