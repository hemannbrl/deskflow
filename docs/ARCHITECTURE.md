# Architecture

deskflow is a help-desk system with a Django REST API, a Next.js web client, and
Celery workers for time-based automation.

```
┌──────────────┐   JWT / JSON    ┌──────────────────┐        ┌────────────┐
│   Next.js    │ ──────────────▶ │   Django + DRF   │ ─────▶ │ PostgreSQL │
│  (frontend/) │                 │    /api/v1/…     │        └────────────┘
└──────────────┘                 └──────────────────┘              ▲
                                                                   │ same model methods
                                 ┌──────────────────┐        ┌────────────┐
                                 │   Celery beat    │ ─────▶ │   worker   │
                                 │ (via Redis)      │        └────────────┘
                                 └──────────────────┘
```

One Django project (`deskflow/`) with one app (`tickets/`), split by responsibility:

| module | responsibility |
|--------|----------------|
| `tickets/models.py` | `Profile`, `Ticket` (+ state machine), `TicketEvent`, `Comment` |
| `tickets/permissions.py` | role helper + object-level access rules |
| `tickets/serializers.py` | API shapes; server-controlled fields are read-only |
| `tickets/views.py` | auth, `/me/`, ticket CRUD + transition actions |
| `tickets/sla.py` | SLA windows and the escalation rule (plain functions) |
| `tickets/tasks.py` | Celery wrappers around the SLA logic |
| `tickets/signals.py` | auto-create a `Profile` for every new user |

## Data model

- **Profile** — one-to-one with `auth_user`; carries the role
  (`requester` / `agent` / `manager`). Created automatically by a `post_save` signal,
  so "every user has a role" holds everywhere.
- **Ticket** — the core record: title, description, priority, category,
  requester/assignee FKs, `status`, `sla_due_at`, and one timestamp per lifecycle
  stage (`escalated_at`, `resolved_at`, `closed_at`). Indexed on `status`,
  `assignee`, and `sla_due_at` (the columns the queues and the SLA sweep filter on).
- **TicketEvent** — append-only audit row per status change: actor (null = the
  system), from/to status, optional note, timestamp.
- **Comment** — per-ticket thread; `is_internal` marks staff-only notes.

## The state machine

```
open ──▶ assigned ──▶ resolved ──▶ closed
  │          │            ▲
  └──────────┴─▶ escalated┘
```

Transitions are **methods on the `Ticket` model** (`assign`, `escalate`, `resolve`,
`close`), all funneled through a single `_transition` chokepoint that:

1. rejects any move not in the `ALLOWED` set (raising `TransitionError`),
2. writes the `TicketEvent` audit row and the status change in **one transaction**.

Views never set `status` directly — the field is read-only in the serializer, and the
action endpoints translate `TransitionError` into a 400 with the reason. Because the
Celery jobs call the same methods, automated changes are audited identically to human
ones (with a null actor).

## Roles and access

Access is enforced twice: querysets scope what a role can *see* (so unauthorized
objects 404 rather than 403), and object permissions guard writes.

| role | sees | can |
|------|------|-----|
| requester | own tickets | create, comment, close their own resolved tickets |
| agent | assigned to them + unassigned queue | self-claim from the queue, resolve their assigned tickets, internal notes |
| manager | everything | assign anyone, escalate, resolve, close |

Escalation is manager-only by hand — otherwise it's the SLA job's. Each action
endpoint enforces its role rule server-side (403 with the reason); the UI only decides
which buttons to render. Internal comments are rejected from requesters on write and
filtered out for them on read.

## SLA automation

Every ticket gets `sla_due_at` at creation from its priority: urgent 4h, high 8h,
normal 24h, low 72h. Two Celery beat jobs run outside the request cycle:

- `run_sla_escalation` (every 5 min) — escalates open/assigned tickets past their
  deadline, with an `sla breach` audit note.
- `auto_close_resolved` (hourly) — closes tickets that sat in `resolved` for 3 days
  without the requester confirming.

The rules live in `tickets/sla.py` as plain, synchronously-tested functions; the tasks
are thin wrappers. Escalation has two triggers — manual (an agent/manager) and
automatic — calling the same model method.

## Frontend

`frontend/` is a Next.js (App Router, TypeScript, Tailwind) SPA-style client. A single
fetch wrapper attaches the JWT and refreshes it once on 401; an auth context restores
the session from `/api/v1/me/`. The UI renders controls based on role and status but
enforces nothing itself — the API stays the single authority, and the client surfaces
its 400s. Tokens live in `localStorage`: a deliberate trade-off (httpOnly cookies
resist XSS better but require a different backend auth flow).

## Cross-cutting choices

- **API versioned** under `/api/v1/`; page-number pagination (20/page); per-user and
  per-anon throttles.
- **Config from the environment** (`.env` via python-dotenv); no secrets in the repo.
- **CI** (GitHub Actions) runs ruff + the Django suite against real Postgres/Redis,
  and lints/builds the frontend, on every push and PR.
