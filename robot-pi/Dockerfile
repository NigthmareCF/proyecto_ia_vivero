FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    liblgpio1 \
    libgpiod2 \
    libatlas-base-dev \
    libopenjp2-7 \
    libtiff6 \
    libgl1 \
    libglib2.0-0 \
    i2c-tools \
    zbar-tools \
    libzbar0 \
    libcamera-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY src ./src
COPY models ./models

RUN mkdir -p /app/models

CMD ["python", "main.py"]
