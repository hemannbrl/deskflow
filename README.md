# deskflow

![CI](https://github.com/hemannbrl/deskflow/actions/workflows/ci.yml/badge.svg)

IT help desk and ticketing API. Requesters open tickets, agents work them, and
managers handle assignment and SLA breaches. Tickets move through a state machine and
escalate automatically when their SLA deadline passes.

## Features

- JWT-authenticated REST API
- Tickets with priority, category, and a status state machine
  (open → assigned → escalated → resolved → closed)
- Role-based access (requester / agent / manager) with role-filtered ticket lists
- Comment threads with internal (agent-only) notes
- Append-only audit trail of every status change (who, what, when)
- Automatic SLA escalation and auto-close of stale resolved tickets via scheduled Celery tasks
- OpenAPI schema + Swagger UI
- Versioned API (`/api/v1/`) with pagination and per-user/anon rate limits
- Next.js web client (`frontend/`) with a role-aware UI: queues, internal notes,
  and state-machine actions

## Tech Stack

- Python 3.14, Django 6.0
- Django REST Framework
- SimpleJWT for authentication
- PostgreSQL (`psycopg2-binary`)
- Celery + Redis for the scheduled SLA escalation job
- drf-spectacular for the OpenAPI schema
- python-dotenv for `.env` config
- ruff + pre-commit + GitHub Actions CI
- Next.js 16, React 19, TypeScript, Tailwind CSS 4 (web client)

## Architecture

Single Django project (`deskflow`) with one app (`tickets`). The ticket status
transitions live as methods on the `Ticket` model so the state machine is enforced in
one place; views call those methods rather than setting `status` directly, and each
transition writes a `TicketEvent` audit row in the same transaction. Two Celery beat
tasks run outside the request cycle: one escalates tickets past their `sla_due_at`, one
auto-closes resolved tickets the requester never confirmed — both calling the same model
methods a user would. Config is read from `.env`.

SLA windows by priority: urgent 4h, high 8h, normal 24h, low 72h.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — components, data model, the state
  machine, roles, and the SLA automation
- [`docs/API.md`](docs/API.md) — endpoint reference with curl examples
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — configuration, production setup, and CI

## Running Locally

Requires PostgreSQL and Redis — start both with `docker compose up -d`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# set DJANGO_SECRET_KEY and POSTGRES_PASSWORD in .env

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Optional: `python manage.py seed_demo` fills the app with demo users and tickets in
every lifecycle state (all demo logins use password `deskflow123`).

In separate terminals, for SLA escalation and auto-close:

```bash
celery -A deskflow worker -l info
celery -A deskflow beat -l info
```

API at http://localhost:8000/, admin at `/admin/`, interactive docs at `/api/docs/`.

To exercise the API: register at `/api/auth/register/`, get a JWT at `/api/auth/token/`,
then open `/api/docs/`, click **Authorize**, and paste the access token.

## Frontend

The web client lives in `frontend/` and talks to the API above:

```bash
cd frontend
npm install
cp .env.local.example .env.local   # API base URL, default http://localhost:8000
npm run dev                        # http://localhost:3000
```

Register as a requester and open tickets; promote a user to agent or manager (via the
admin or shell) to see the queue, internal notes, and the assign/escalate/resolve/close
actions. The UI only decides which controls to *render* — every rule is enforced by the
API, and the client surfaces its errors.

Auth note: JWTs are kept in `localStorage` with an automatic refresh-and-retry on 401.
That's a deliberate simplification — httpOnly cookies would resist XSS better but need a
different backend auth flow; for this project the SPA-style token flow keeps the API
unchanged.

## Running Tests

```bash
python manage.py test

# with coverage
coverage run manage.py test && coverage report
```

## API Endpoints

```
POST   /api/auth/register/          register a user
POST   /api/auth/token/             obtain JWT
POST   /api/auth/token/refresh/     refresh JWT

GET    /api/v1/me/                     current user + role

GET    /api/v1/tickets/                list (role-filtered, paginated)
POST   /api/v1/tickets/                create
GET    /api/v1/tickets/{id}/           retrieve
PATCH  /api/v1/tickets/{id}/           update

POST   /api/v1/tickets/{id}/assign/    -> assigned
POST   /api/v1/tickets/{id}/escalate/  -> escalated
POST   /api/v1/tickets/{id}/resolve/   -> resolved
POST   /api/v1/tickets/{id}/close/     -> closed

GET    /api/v1/tickets/{id}/events/    audit history
GET    /api/v1/tickets/{id}/comments/  list thread
POST   /api/v1/tickets/{id}/comments/  add comment

GET    /api/schema/                 OpenAPI schema
GET    /api/docs/                   Swagger UI
```

## What I Learned

- **Put state transitions on the model, not in views.** Routing every status change
  through one guarded `_transition` method meant the API endpoints, the Celery tasks,
  and the admin all obey the same rules, and the audit trail can't be skipped.
- **Prove background logic synchronously first.** The SLA escalation was written and
  tested as a plain function before Celery ever touched it — the beat task ended up
  being a two-line wrapper, and the tests don't need a broker.
- **Read-only serializer fields are a security boundary.** Making `status`, `assignee`,
  and the timestamps read-only forces every mutation through the action endpoints,
  where the permission and transition checks live.
- **Role scoping belongs in `get_queryset`.** Filtering the queryset by role means
  unauthorized objects 404 instead of 403, and list/detail views stay consistent
  without repeating checks.
- **Signals for invariants.** Auto-creating a `Profile` on user creation keeps
  "every user has a role" true everywhere — tests, admin, shell — without remembering
  to call anything.
- **The UI offers, the API decides.** The frontend renders buttons based on role and
  status, but never enforces a rule itself — illegal moves still get a 400 from the
  server, and the client just shows it. One authority, no drift.
