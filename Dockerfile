FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY backend /app/backend

WORKDIR /app/backend

ENV DJANGO_SETTINGS_MODULE=credit_system.settings

CMD ["gunicorn", "credit_system.wsgi:application", "--bind", "0.0.0.0:8000"]

