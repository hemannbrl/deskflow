# Deployment

## Configuration

All configuration is environment-driven (loaded from `.env` in development —
see `.env.example`). No secret is committed.

| variable | purpose | dev default |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | Django signing key — generate per environment | *(required)* |
| `DJANGO_DEBUG` | `True`/`False` | `False` |
| `DJANGO_ALLOWED_HOSTS` | comma-separated hosts | *(empty)* |
| `POSTGRES_DB/USER/PASSWORD/HOST/PORT` | database | `deskflow`/`postgres`/…/`localhost`/`5432` |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis | `redis://localhost:6379/0` and `/1` |
| `REDIS_CACHE_URL` | shared cache (throttle counters) | `redis://localhost:6379/2` |
| `CORS_ALLOWED_ORIGINS` | comma-separated frontend origins | *(empty — nothing allowed)* |
| `DJANGO_SECURE_SSL_REDIRECT` | force HTTPS behind the proxy | `False` |
| `DJANGO_HSTS_SECONDS` | HSTS max-age (enables preload when > 0) | `0` |
| `NEXT_PUBLIC_API_URL` | (frontend) API base URL | `http://localhost:8000` |

## Local development

```bash
docker compose up -d                  # Postgres 16 + Redis 7
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env                  # set SECRET_KEY and POSTGRES_PASSWORD
python manage.py migrate
python manage.py runserver            # API on :8000

celery -A deskflow worker -l info     # separate terminals: SLA jobs
celery -A deskflow beat -l info

cd frontend && npm install && cp .env.local.example .env.local && npm run dev  # :3000
```

Optional: `python manage.py seed_demo` populates demo users and tickets in every
lifecycle state (wipes existing tickets; all demo users get password `deskflow123`).

## Production

The API ships as a container (see `Dockerfile`): `python:3.14-slim`, gunicorn on
`:8000`, WhiteNoise serving static files with compressed manifests. Run migrations and
collectstatic at **deploy** time, not build time (they need the environment and DB):

```bash
docker build -t deskflow .
# at deploy:
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn deskflow.wsgi:application --bind 0.0.0.0:8000
```

Run four processes against the same env: **gunicorn**, **celery worker**,
**celery beat** (one instance only), and the **frontend** (`next build && next start`,
or any static/Node host) with `NEXT_PUBLIC_API_URL` pointing at the API and the
frontend origin added to `CORS_ALLOWED_ORIGINS`.

### Security posture

With `DJANGO_DEBUG=False`, secure cookies switch on automatically; set
`DJANGO_SECURE_SSL_REDIRECT=True` and `DJANGO_HSTS_SECONDS` (e.g. `31536000`) behind
TLS. The proxy SSL header is honored (`X-Forwarded-Proto`). Verify a clean:

```bash
DJANGO_DEBUG=False python manage.py check --deploy
```

The API is versioned (`/api/v1/`), paginated, and throttled (per-user and per-anon
rates) out of the box.

## CI

`.github/workflows/ci.yml` runs on every push and PR:

- **backend** — ruff lint + format check, migrations, and the test suite with
  coverage (fails under 85%) against real Postgres 16 and Redis 7 service containers.
- **frontend** — `npm ci`, ESLint, production build on Node 22.

Pre-commit hooks (ruff, ruff-format, whitespace/EOF/YAML checks) enforce the same
standards locally: `pre-commit install`.
