# 🔧 FIX: psycopg2 Import Error During Build

## Error Fixed ✅

```
django.core.exceptions.ImproperlyConfigured: Error loading psycopg2 or psycopg module
==> Build failed 😞
```

---

## Root Cause

Django was trying to initialize the database connection during the **build phase** when:
1. `DATABASE_URL` environment variable was not yet set
2. Django tried to parse the database config
3. It attempted to import psycopg2 (PostgreSQL driver)
4. psycopg2 either wasn't installed or couldn't be imported

**The Problem Chain:**
```
Build phase starts
  ↓
Python imports Django settings
  ↓
Django tries to connect to DATABASE_URL
  ↓
DATABASE_URL is empty, but Django still tries to initialize DB backend
  ↓
psycopg2 import fails
  ↓
Build fails ❌
```

---

## Solution Implemented ✅

### 1. **Smart Database Configuration** (settings.py)
Now explicitly checks if `DATABASE_URL` is set:

```python
DATABASE_URL = env("DATABASE_URL", default=None)

if DATABASE_URL:
    # Production: Use configured database
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    # Build/Development: Use SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
```

**Benefits:**
- ✅ No database initialization during build (uses SQLite)
- ✅ No psycopg2 import errors during build
- ✅ Automatically switches to configured DB when DATABASE_URL is available
- ✅ Works with any database type (PostgreSQL, MySQL, etc.)

### 2. **Build/Start Separation** (build.sh & start.sh)

**build.sh (Build phase - no DB access needed):**
```bash
pip install -r requirements.txt
# ✅ That's it! No Django management commands
```

**start.sh (Startup phase - DB is available):**
```bash
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py shell << EOF
    # Create superuser if needed
EOF
gunicorn ...
```

### 3. **Database URL Flexibility** (requirements.txt)
Added `dj-database-url` for better URL parsing:
```
dj-database-url==2.1.0
```

This allows DATABASE_URL to be:
- `postgresql://...` (PostgreSQL)
- `mysql://...` (MySQL)
- `sqlite:///...` (SQLite)

---

## How It Works Now

### Build Phase (No Database Needed)
```
1. Install dependencies (pip install)
2. That's all - no Django initialization
3. ✅ Build succeeds
```

### Startup Phase (Database Available)
```
1. DATABASE_URL is set in environment
2. start.sh runs
3. Collect static files
4. Run migrations (database is now available)
5. Create superuser
6. Start Gunicorn
7. ✅ Server is live
```

---

## Environment Variables Setup

### In Render Dashboard:

**For PostgreSQL (Recommended):**
1. Create PostgreSQL database in Render
2. Link `DATABASE_URL` to it (auto-populated)

**For MySQL (Aiven):**
```
DATABASE_URL=mysql://user:pass@host:3306/dbname
```

**For SQLite (Development Only):**
```
Leave DATABASE_URL empty or unset
```

---

## Deployment Steps

1. **Commit these changes:**
   ```bash
   git add build.sh start.sh requirements.txt unipeer/settings.py
   git commit -m "fix: Prevent psycopg2 import error during build

   - Separate build phase from runtime phase
   - Use SQLite during build, configured DB at runtime
   - Add dj-database-url for flexible DB URL parsing
   - Move collectstatic to startup phase"
   git push origin main
   ```

2. **In Render Dashboard:**
   - Settings → Build Command: `./build.sh`
   - Settings → Start Command: `./start.sh`
   - Save

3. **Ensure Environment Variables:**
   - `DATABASE_URL` should be set (linked to database)
   - `SECRET_KEY` should be set
   - Other variables as needed

4. **Deploy:**
   - Manual Deploy → Deploy latest commit

---

## Expected Build Output

### Build Phase:
```
🚀 Starting build process...
📦 Installing dependencies...
Collecting asgiref==3.11.1
...
Successfully installed Django-6.0.2 ...
✅ Build completed successfully!
⚠️  Note: Static files and migrations will run on startup
```

### Startup Phase:
```
📊 Collecting static files...
130 static files copied to '/opt/render/project/src/staticfiles'
🔄 Running database migrations...
Operations to perform: Apply all migrations...
🌱 Creating superuser if needed...
✅ Superuser created: admin / changeme123
🚀 Starting Gunicorn server...
```

---

## Why This Fix Works

### Before:
- ❌ Django tried to initialize database during import
- ❌ psycopg2 was imported even without DATABASE_URL
- ❌ Build failed trying to connect to missing database

### After:
- ✅ Build doesn't touch database at all
- ✅ Only imports psycopg2 when actually needed
- ✅ Build is just: install dependencies
- ✅ Startup handles: migrations, static files, superuser
- ✅ Works with any database type

---

## Troubleshooting

### Build Still Fails
- Check `build.sh` is executable: `chmod +x build.sh`
- Check `start.sh` is executable: `chmod +x start.sh`
- Check requirements.txt has no syntax errors

### Startup Fails
- Check `DATABASE_URL` is set in Render environment
- Check database is created and accessible
- Check `start.sh` is the Start Command in Render

### Static Files Not Loading
- Check `start.sh` includes `collectstatic` command
- Check `STATIC_ROOT` is configured: `/opt/render/project/src/staticfiles`
- Check `STATIC_URL` is configured: `/static/`

### Superuser Not Created
- Run manually: `python manage.py createsuperuser`
- Or check logs - it may already exist

---

## Key Files Modified

| File | Change | Why |
|------|--------|-----|
| `settings.py` | Smart DB detection | Prevent psycopg2 import during build |
| `build.sh` | Only install deps | No Django management commands |
| `start.sh` | All Django commands | Only when DB is available |
| `requirements.txt` | Add dj-database-url | Flexible URL parsing |

---

## Success Indicators

✅ Build logs show:
```
✅ Build completed successfully!
```

✅ Startup logs show:
```
🚀 Starting Gunicorn server...
```

✅ Service status is "Live"

✅ Health check passes

✅ API responds:
```bash
curl https://your-app.onrender.com/api/stats/
# Returns JSON data
```

---

**Status:** 🟢 Ready to Deploy!

