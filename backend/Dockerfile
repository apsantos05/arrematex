# ── Estágio 1: builder ──────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev libxml2-dev libxslt-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements/base.txt requirements/production.txt ./requirements/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements/production.txt

# ── Estágio 2: runtime ───────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Cria usuário não-root
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

RUN mkdir -p /app/media /app/static && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["sh", "-c", \
  "python manage.py migrate --noinput && \
   python manage.py collectstatic --noinput && \
   gunicorn config.asgi:application \
     -k uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:8000 \
     --workers 4 \
     --timeout 120 \
     --access-logfile - \
     --error-logfile -"]
