# API reference

Base URL: `http://localhost:8000` in development. Interactive docs (Swagger UI) at
`/api/docs/`, raw OpenAPI schema at `/api/schema/`.

All endpoints except registration and token issuance require
`Authorization: Bearer <access>`.

## Authentication

```bash
# register (new users are requesters; roles are elevated by an admin)
curl -X POST localhost:8000/api/auth/register/ \
  -d 'username=joe&password=secret123'
# → 201 {"id":7,"username":"joe","email":""}

# obtain a token pair
curl -X POST localhost:8000/api/auth/token/ \
  -d 'username=joe&password=secret123'
# → 200 {"refresh":"…","access":"…"}

# refresh an expired access token
curl -X POST localhost:8000/api/auth/token/refresh/ -d 'refresh=…'

# who am I
curl localhost:8000/api/v1/me/ -H "Authorization: Bearer $TOKEN"
# → 200 {"id":7,"username":"joe","email":"","role":"requester"}
```

## Endpoints

```
POST   /api/auth/register/             create an account
POST   /api/auth/token/                obtain JWT pair
POST   /api/auth/token/refresh/        refresh the access token
GET    /api/v1/me/                     current user + role

GET    /api/v1/tickets/                list — role-scoped, paginated
POST   /api/v1/tickets/                create
GET    /api/v1/tickets/{id}/           retrieve
PATCH  /api/v1/tickets/{id}/           update editable fields

POST   /api/v1/tickets/{id}/assign/    open → assigned   {"assignee": <user id>}
POST   /api/v1/tickets/{id}/escalate/  → escalated       {"note": "…"} (optional)
POST   /api/v1/tickets/{id}/resolve/   → resolved
POST   /api/v1/tickets/{id}/close/     resolved → closed

GET    /api/v1/tickets/{id}/events/    audit history, oldest first
GET    /api/v1/tickets/{id}/comments/  thread (internal notes hidden from requesters)
POST   /api/v1/tickets/{id}/comments/  {"body": "…", "is_internal": false}
```

List responses are paginated: `{"count", "next", "previous", "results"}`, 20 per page,
`?page=N`.

## Tickets

Create with `title`, `description`, and optionally `priority`
(`low|normal|high|urgent`, default `normal`) and `category`. The server sets
everything else — requester, status (`open`), and `sla_due_at` from the priority
window (urgent 4h / high 8h / normal 24h / low 72h):

```bash
curl -X POST localhost:8000/api/v1/tickets/ -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"vpn down","description":"cannot connect","priority":"high"}'
```

`status`, `assignee`, and the lifecycle timestamps are **read-only** — they only change
through the action endpoints, so the state machine can't be bypassed with a `PATCH`.

Who sees what on the list: requesters their own tickets, agents their assigned plus
the unassigned queue, managers everything. Objects outside your scope return 404.

## Transitions and errors

Legal moves: `open→assigned`, `open/assigned→escalated`, `assigned/escalated→resolved`,
`resolved→closed`. An illegal move is a 400 with the reason:

```bash
curl -X POST localhost:8000/api/v1/tickets/1/close/ -H "Authorization: Bearer $TOKEN"
# → 400 {"detail":"cannot go open -> closed"}
```

Every successful transition appends an audit event (visible at `…/events/`) recording
actor, from/to status, an optional note, and the time. Events with a null actor were
made by the system (SLA escalation, auto-close).

## Rate limits

1000 requests/day per authenticated user; 20/hour for anonymous callers
(registration and token endpoints). Exceeding them returns 429.
