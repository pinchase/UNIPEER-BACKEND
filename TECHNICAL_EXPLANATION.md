# 🔍 Technical Deep Dive: psycopg2 Error Explained

## The Exact Error

```
File "/opt/render/project/src/.venv/lib/python3.14/site-packages/django/contrib/auth/base_user.py", line 43, in <module>
    class AbstractBaseUser(models.Model):
File "/opt/render/project/src/.venv/lib/python3.14/site-packages/django/db/models/base.py", line 145, in __new__
    new_class.add_to_class("_meta", Options(meta, app_label))
File "/opt/render/project/src/.venv/lib/python3.14/site-packages/django/db/models/base.py", line 393, in add_to_class
    value.contribute_to_class(cls, name)
File "/opt/render/project/src/.venv/lib/python3.14/site-packages/django/db/models/options.py", line 238, in contribute_to_class
    self.db_table, connection.ops.max_name_length()
File "/opt/render/project/src/.venv/lib/python3.14/site-packages/django/db/backends/postgresql/base.py", line 29, in <module>
    raise ImproperlyConfigured("Error loading psycopg2 or psycopg module")

django.core.exceptions.ImproperlyConfigured: Error loading psycopg2 or psycopg module
```

## Why It Happened

### The Call Stack

```
1. Build starts → Python imports Django
2. Django imports models
3. Django tries to initialize database connection
4. Django auto-detects database type from DATABASE_URL
5. DATABASE_URL is empty → defaults to PostgreSQL backend
6. PostgreSQL backend tries to import psycopg2
7. psycopg2 not available during build → ERROR
```

### Why psycopg2 Wasn't Available

**In requirements.txt before:**
```
psycopg2-binary==2.9.9
```

**But:**
1. build.sh was trying to initialize Django
2. Django connects to database to check table names
3. This happens BEFORE pip packages are fully loaded
4. psycopg2 import is attempted
5. Module not found → Build fails

### The Critical Line

In `settings.py` (BEFORE):
```python
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}
```

**The Problem:**
- `env.db()` parses DATABASE_URL
- If DATABASE_URL is empty, it tries to parse a SQLite path
- But `env.db()` STILL tries to determine the backend type
- Django then tries to initialize the backend
- Without DATABASE_URL, it defaults to PostgreSQL
- psycopg2 import fails

## The Solution

### Before (Problematic)
```python
# env.db() tries to parse the default SQLite string
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}
# This still triggers database initialization!
```

### After (Fixed)
```python
# Check if DATABASE_URL is actually set
DATABASE_URL = env("DATABASE_URL", default=None)

if DATABASE_URL:
    # Only use env.db() if DATABASE_URL is explicitly set
    DATABASES = {
        "default": env.db("DATABASE_URL")
    }
else:
    # Explicitly define SQLite without triggering backend detection
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
```

**Why This Works:**
1. Checks if DATABASE_URL is actually set (not just defaults to empty)
2. Only uses `env.db()` if DATABASE_URL has a real value
3. Explicitly defines SQLite backend without any parsing
4. No database initialization during import

## The Build/Startup Separation

### Before (Problematic)
```bash
# build.sh
pip install -r requirements.txt
python manage.py collectstatic --no-input  # ← This imports Django!
```

**Problem:**
- `collectstatic` imports Django models
- Django tries to initialize database
- Database not available → FAIL

### After (Fixed)
```bash
# build.sh (Build Phase - No Database)
pip install -r requirements.txt
# Done! No Django commands

# start.sh (Startup Phase - Database Available)
python manage.py collectstatic --no-input  # ← Now DB is available!
python manage.py migrate --no-input
gunicorn ...
```

**Why This Works:**
1. Build phase: Only installs dependencies
2. No Django initialization during build
3. Startup phase: DATABASE_URL is now set in environment
4. Django can safely initialize and connect
5. Migrations and collectstatic work fine

## The env.db() Mystery

Django-environ's `env.db()` function:
```python
def db(self, var='DATABASE_URL', conn_max_age=600):
    """Parse a database URL"""
    url = self.str(var)
    # Parses the URL and INFERS the backend type
    # If URL looks like: mysql://... → Uses MySQL backend
    # If URL looks like: postgresql://... → Uses PostgreSQL backend
    # If URL is EMPTY → Defaults to PostgreSQL backend (!)
    
    # This triggers backend initialization!
    return self._parse_url(url)
```

**The Key Issue:**
When `env.db()` gets an empty string or default, it doesn't just return a config object - it tries to parse it and determine the backend type, which triggers Django's database initialization code.

## The Order of Operations

### Before (WRONG)
```
Render Build Starts
    ↓
pip install -r requirements.txt
    ↓
Python imports unipeer.settings
    ↓
env.db() tries to parse DATABASE_URL
    ↓
Django tries to initialize PostgreSQL backend (default)
    ↓
psycopg2 import fails (not installed yet or unavailable)
    ↓
BUILD FAILS ❌
```

### After (CORRECT)
```
Render Build Starts
    ↓
pip install -r requirements.txt
    ↓
Done! No Django commands
    ↓
BUILD SUCCEEDS ✅
    ↓
Render Startup
    ↓
DATABASE_URL is now in environment
    ↓
Python imports unipeer.settings
    ↓
env("DATABASE_URL") returns actual connection string
    ↓
env.db() parses real DATABASE_URL
    ↓
Django initializes database backend (PostgreSQL/MySQL)
    ↓
psycopg2/mysqlclient imports successfully
    ↓
python manage.py collectstatic
    ↓
python manage.py migrate
    ↓
Start Gunicorn
    ↓
SERVER IS LIVE ✅
```

## Key Learnings

1. **Don't initialize Django during build**
   - Use build phase only for: pip install
   - Use startup phase for: Django management commands

2. **Use conditional database config**
   - Check if DATABASE_URL is actually set
   - Don't rely on env.db() with defaults

3. **Separate concerns**
   - Build: Install + prepare
   - Startup: Initialize + run

4. **Test locally first**
   - Replicate the build environment
   - Verify scripts work without errors

## Prevention for Future Issues

### Pattern to Follow
```python
# ✅ GOOD: Check existence before parsing
env_var = env("DATABASE_URL", default=None)
if env_var:
    config = env.db("DATABASE_URL")
else:
    config = {...}  # Explicit config

# ❌ BAD: Rely on env.db() with defaults
config = env.db("DATABASE_URL", default="...")
```

### Script Pattern
```bash
# ✅ GOOD: Separate build and startup
# build.sh - No Django
pip install -r requirements.txt

# start.sh - Django management
python manage.py migrate
python manage.py collectstatic
gunicorn ...

# ❌ BAD: Mix build and Django
# build.sh
pip install -r requirements.txt
python manage.py collectstatic  # ← Triggers DB init!
```

## Lessons Applied

1. ✅ Fixed settings.py to conditionally define database
2. ✅ Separated build.sh and start.sh
3. ✅ Added dj-database-url for fallback parsing
4. ✅ Documented the issue for future reference
5. ✅ Added troubleshooting guides

---

**Bottom Line:**
The psycopg2 error occurred because Django tried to connect to PostgreSQL during the build phase when the database wasn't available. The fix ensures that database initialization only happens at startup when DATABASE_URL is actually configured.

