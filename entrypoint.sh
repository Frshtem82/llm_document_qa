#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL..."
while ! python -c "
import psycopg2
import os
try:
    psycopg2.connect(
        dbname=os.environ.get('DB_NAME', 'llm_project'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgres'),
        host=os.environ.get('DB_HOST', 'db'),
        port=os.environ.get('DB_PORT', '5432'),
    )
    print('✅ PostgreSQL is ready')
except Exception as e:
    print('❌ PostgreSQL not ready:', e)
    exit(1)
"; do
    sleep 2
done

echo "🔄 Running migrations..."
python manage.py migrate --noinput

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput || true

echo "🚀 Starting Django..."
exec "$@"