#!/usr/bin/env bash
# Startup script for Render.com - runs migrations and starts server

echo "📊 Collecting static files..."
python manage.py collectstatic --no-input

echo "🔄 Running database migrations..."
python manage.py migrate --no-input

echo "🌱 Creating superuser if needed..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'changeme123')
    print('✅ Superuser created: admin / changeme123')
else:
    print('ℹ️ Superuser already exists')
EOF

echo "👥 Checking if seed data is needed..."
python manage.py shell << EOF
from django.contrib.auth.models import User
import os
import subprocess

user_count = User.objects.count()

if user_count <= 1:
    print("🌱 Database looks empty. Seeding 50 student profiles...")
    subprocess.run(["python", "manage.py", "seed_unipeer"])
else:
    print(f"ℹ️ Database already has {user_count} users. Skipping seed.")
EOF

echo "🚀 Starting Gunicorn server..."
exec gunicorn unipeer.wsgi:application --bind 0.0.0.0:$PORT