# Dockerfile
FROM python:3.11-slim

# تنظیمات محیطی
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITE=BYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# نصب وابستگی‌های سیستم (برای psycopg2 و jdatetime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# دایرکتوری کاری
WORKDIR /app

# کپی requirements و نصب اول
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی بقیه کدها
COPY . .

# اجرای ربات
CMD ["python", "main.py"]
