#!/usr/bin/env bash
# Startup script for Render.com - runs migrations and starts server

echo "📊 Collecting static files..."
python manage.py collectstatic --no-input

echo "🔄 Running database migrations..."
python manage.py migrate --no-input

echo "🌱 Creating superuser if needed..."
# This will only create if it doesn't exist
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'changeme123')
    print('✅ Superuser created: admin / changeme123')
else:
    print('ℹ️  Superuser already exists')
EOF

echo "🚀 Starting Gunicorn server..."
exec gunicorn unipeer.wsgi:application --bind 0.0.0.0:$PORT

