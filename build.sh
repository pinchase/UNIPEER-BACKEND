#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Starting build process..."

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "📊 Collecting static files..."
# Collect static files (Django will use SQLite for this, no DB connection needed)
python manage.py collectstatic --no-input

echo "✅ Build completed successfully!"
echo "⚠️  Note: Migrations will run on startup when DATABASE_URL is available"

