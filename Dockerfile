FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /home/app app

COPY requirements/ ./requirements/

RUN pip install --upgrade pip \
    && pip install -r requirements/production.txt

COPY scripts/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

COPY . .

RUN python manage.py collectstatic --noinput \
    && chown -R app:app /app /home/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/', timeout=3).read()"

USER app

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn"]
