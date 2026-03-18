# UniPeer Backend

A Django + Django REST Framework + Channels backend powering UniPeer — a student collaboration network with profiles, ML-based matching & recommendations, realtime chat, gamification, and notification flows.

Why this repo

- Centralized student profiles with skills, courses, availability, XP/levels and badges.
- Machine-learning helpers for peer/resource recommendations (TF-IDF + cosine similarity with heuristics).
- REST API for frontend-driven apps plus WebSocket collaboration rooms backed by Channels.

Key features

- Student profiles and CRUD endpoints for skills, courses, resources, rooms, matches, and notifications.
- Authentication: JWT (SimpleJWT) for API and query-string JWT support for WebSockets.
- Realtime collaboration: `ws://<host>/ws/rooms/<room_id>/?token=<JWT>` and `RoomChatConsumer` for message persistence and broadcast.
- ML ranking: `api/ml_engine.py` provides `StudentMatcher` and `ResourceRecommender` using TF-IDF + cosine similarity and domain heuristics.
- Gamification: XP, levels, badges; badge data can be seeded with management commands.
- Email flows: OTP-based verification and password reset via Resend (when configured).

Stack

- Django 6, Django REST Framework, drf-spectacular (OpenAPI)
- Channels 4 with optional Redis channel layer (set via `REDIS_URL`)
- PostgreSQL (recommended) or SQLite via `DATABASE_URL`/`django-environ`
- Scikit-learn for TF-IDF and cosine similarity
- WhiteNoise for static files; Resend for transactional emails
- Gunicorn with Uvicorn worker for ASGI in production

Quickstart (local development)

1. Create a virtualenv and activate it (example):
   python -m venv .venv && source .venv/bin/activate
2. Install dependencies:
   pip install -r requirements.txt
3. Copy the env template and adjust values:
   cp .env .env.local
4. Run migrations and prepare static files:
   python manage.py migrate
   python manage.py collectstatic --no-input
5. (Optional) Seed demo data:
   python manage.py seed_badges
   python manage.py seed_data
6. Start the dev server (ASGI-ready):
   python manage.py runserver

Environment variables (high level)

- SECRET_KEY: Django secret (required in prod)
- DEBUG: Set to `False` in production
- ALLOWED_HOSTS: Comma-separated hosts
- DATABASE_URL: If absent, uses SQLite `db.sqlite3`
- REDIS_URL: If present, enables Redis channel layer for Channels
- RESEND_API_KEY: API key for Resend email service
- DEFAULT_FROM_EMAIL: Defaults to `UniPeer <noreply@mail.unipeer.me>`
- EMAIL\_\*: Optional SMTP overrides (password defaults to `RESEND_API_KEY`)

Common management commands

- python manage.py makemigrations
- python manage.py migrate
- python manage.py seed_badges
- python manage.py seed_data
- python manage.py test
- python manage.py collectstatic --no-input
- python manage.py runserver

API highlights

- REST endpoints (viewsets): /api/skills, /api/courses, /api/profiles, /api/resources, /api/rooms, /api/notifications, /api/matches
- Auth & account: /api/register/, /api/login/, /api/token/refresh/
- Email flows: /api/verify-email/, /api/resend-verification/, /api/password-reset/request/, /api/password-reset/confirm/
- Extras: /api/stats/, /api/keep-alive/, /api/whoami/
- Schema & docs: /api/schema/, /api/docs/, /api/redoc/ (drf-spectacular)

Realtime collaboration

- WebSocket path: ws://<host>/ws/rooms/<room_id>/?token=<JWT>
- Authentication: custom JWT query-string middleware implemented in `api/ws_auth.py`
- Consumer: `RoomChatConsumer` validates membership, stores `Message` objects, and broadcasts to a Channels group
- Direct rooms: matched students share persistent two-member direct rooms via `get_or_create_direct_room`

Machine learning & recommendations

- `api/ml_engine.py` vectorizes profile/resource feature text with `TfidfVectorizer` and ranks with cosine similarity.
- Heuristics boost results for shared courses, skills, department/year, schedules, preferences, ratings and popularity.
- Dashboard endpoints include top matches and recommended resources with human-readable reasons.

Deployment notes

- build.sh installs dependencies; start.sh is Render-ready and runs collectstatic/migrate/create-superuser before launching Gunicorn.
- Procfile starts Gunicorn with a Uvicorn worker so Channels works in production.
- See `RENDER_DEPLOYMENT_GUIDE.md`, `DEPLOYMENT_CHECKLIST.md`, `DEPLOY_NOW.md`, and `FINAL_DEPLOYMENT.md` for environment- and provider-specific steps.
- For Redis-backed Channels in production, set `REDIS_URL` and verify connectivity before enabling WebSockets.

Testing & quality

- Run the test suite: `python manage.py test`.
- No bundled linting in repo; recommended dev tools: ruff, black, isort, mypy.

Contributing / next steps for developers

1. When adding fields, update `api/serializers.py` and `api/views.py` to keep API contracts stable.
2. Keep `api/ml_engine.py` and `StudentProfile.get_feature_text` aligned when adding profile attributes to preserve recommendation quality.
3. Document new WebSocket message types and update `RoomChatConsumer.receive` when adding real-time commands.

Where to look next

- `api/` for models, serializers, views, consumers and ML helpers.
- `management/commands/` for seeding scripts.
- `unipeer/settings.py` for environment configuration and CORS setup.

License & contact

- This repository is intended for the UniPeer project. See repository metadata for license and ownership details.

Happy building!
