
FROM python:3.13-slim

# Prevent Python from buffering logs (so you see them in real-time)
ENV PYTHONUNBUFFERED=1

# Install system tools for Postgres and PDF processing
RUN apt-get update && apt-get install -y \
    libpq-dev \
    build-essential \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install your dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy your code into the container
COPY . .

# Django default port
EXPOSE 8000

