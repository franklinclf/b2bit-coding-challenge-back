#!/bin/sh

set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z $POSTGRES_HOST ${POSTGRES_PORT:-5432}; do
  sleep 0.1
done
echo "PostgreSQL is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z ${REDIS_HOST:-localhost} ${REDIS_PORT:-6379}; do
  sleep 0.1
done
echo "Redis is ready!"

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput

  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

# Create superuser if environment variables are set
if [ "${CREATE_SUPERUSER:-false}" = "true" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --noinput --email "$DJANGO_SUPERUSER_EMAIL" || true
fi

exec "$@"
