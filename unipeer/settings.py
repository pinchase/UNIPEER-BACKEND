"""
Django settings for UniPeer project (Production Ready)
"""

from pathlib import Path
import os
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------
# ENVIRONMENT
# -----------------------------
env = environ.Env(DEBUG=(bool, False))

# Load .env locally (Render uses real env vars)
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)

# -----------------------------
# CORE SECURITY
# -----------------------------
SECRET_KEY = env("SECRET_KEY")

DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[".onrender.com", "localhost", "127.0.0.1"]
)

# -----------------------------
# APPLICATIONS
# -----------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "api",
]

# -----------------------------
# MIDDLEWARE
# -----------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # you can add BASE_DIR / "templates" if you have custom templates
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # REQUIRED for admin
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ROOT_URLCONF = "unipeer.urls"
WSGI_APPLICATION = "unipeer.wsgi.application"

# -----------------------------
# DATABASE
# -----------------------------
DATABASES = {
    "default": env.db("DB_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

# Aiven requires SSL
if "aivencloud.com" in DATABASES["default"]["HOST"]:
    DATABASES["default"]["OPTIONS"] = {
        "ssl": {
            "ca": BASE_DIR / "ca.pem",
        }
    }

# -----------------------------
# PASSWORD VALIDATION
# -----------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -----------------------------
# INTERNATIONALIZATION
# -----------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -----------------------------
# STATIC FILES
# -----------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# -----------------------------
# MEDIA FILES
# -----------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -----------------------------
# DJANGO REST FRAMEWORK
# -----------------------------
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny"
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# -----------------------------
# CORS
# -----------------------------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

if DEBUG and not CORS_ALLOWED_ORIGINS:
    CORS_ALLOW_ALL_ORIGINS = True

# -----------------------------
# SECURITY (Production Hardened)
# -----------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"