FROM python:3.11-alpine

RUN mkdir /app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.8.3
ENV POETRY_VIRTUALENVS_CREATE=false

RUN apk add --no-cache \
    gcc \
    python3-dev \
    musl-dev \
    libmagic \
    libffi-dev \
    netcat-openbsd \
    build-base \
    postgresql-dev \
    && rm -rf /var/cache/apk/*

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock /app/

RUN poetry lock --no-interaction --no-ansi \
    && poetry install --no-interaction --no-ansi --without dev

# Keep requirements.txt available for external tooling while Poetry installs deps in the image.
COPY requirements.txt /app/


COPY ./docker/dev/entrypoint.sh /entrypoint.sh

RUN adduser -D -s /bin/sh appuser \
    && chown -R appuser:appuser /app \
    && chmod +x /entrypoint.sh

USER appuser

COPY . /app/

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python manage.py check || exit 1

ENTRYPOINT [ "/entrypoint.sh" ]