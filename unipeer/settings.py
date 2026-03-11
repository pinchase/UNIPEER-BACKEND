"""
Django settings for UniPeer project (Production Ready)
"""

from pathlib import Path
import os
import environ
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------
# ENVIRONMENT
# -----------------------------
env = environ.Env(DEBUG=(bool, False))

# Load .env locally (Render uses real env vars)
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)


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
    "corsheaders",  # ✅ required for CORS
    "rest_framework",
    "drf_spectacular",
    "api",
]


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # ✅ must be at top
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -----------------------------
# TEMPLATES
# -----------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # add BASE_DIR / "templates" if needed
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
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
DATABASE_URL = env("DATABASE_URL", default=None)

if DATABASE_URL:
    DATABASES = {
        "default": env.db("DATABASE_URL")
    }
    # ✅ Render PostgreSQL SSL
    if DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
        DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
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

# ✅ Optional static files dirs
_optional_static_dir = BASE_DIR / "static"
STATICFILES_DIRS = [_optional_static_dir] if _optional_static_dir.exists() else []

# -----------------------------
# MEDIA FILES
# -----------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -----------------------------
# DJANGO REST FRAMEWORK
# -----------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated"
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "notifications_anon": "120/hour",
        "notifications_user": "1200/hour",
        "notifications_burst": "20/minute",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "UniPeer API",
    "DESCRIPTION": "API documentation for UniPeer backend",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# JWT Settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# -----------------------------
# CORS CONFIGURATION
# -----------------------------
def get_allowed_origins():
    origins = [
        "https://unipeer-frontend.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://0.0.0.0:5500",
    ]
    return origins

CORS_ALLOWED_ORIGINS = get_allowed_origins()

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
    r"^http://0\.0\.0\.0:\d+$",
    r"^https://localhost:\d+$",
    r"^https://127\.0\.0\.1:\d+$",
    r"^https://0\.0\.0\.0:\d+$",
]

# ✅ Credentials only needed for session cookies
CORS_ALLOW_CREDENTIALS = False

# -----------------------------
# SECURITY (Production Hardened)
# -----------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

CSRF_TRUSTED_ORIGINS = [
    "https://unipeer-frontend.vercel.app",
    "https://*.vercel.app",
]

if DEBUG:
    CSRF_TRUSTED_ORIGINS.extend([
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:5500",
    ])

# -----------------------------
# DEFAULT AUTO FIELD
# -----------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------------------
# EMAIL (Verification)
# -----------------------------
RESEND_API_KEY = env("RESEND_API_KEY", default="")

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="UniPeer <noreply@mail.unipeer.me>")
EMAIL_HOST = env("EMAIL_HOST", default="smtp.resend.com" if not DEBUG else "")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="resend" if not DEBUG else "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default=RESEND_API_KEY)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
