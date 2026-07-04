# deskflow — database

Plain map of the tables. Django creates `<app>_<model>` table names, so the app is
`tickets`. `auth_user` is Django's built-in user table; we point at it rather than
redefine it.

## Tables at a glance

```
auth_user (Django)
   │  1─1
tickets_profile        role per user
   │
   │  requester / assignee / author / actor (FKs back to auth_user)
   ▼
tickets_ticket ──1─*── tickets_comment
       │
       └──1─*── tickets_ticketevent     (audit history)
```

## tickets_profile
One row per user, holding their role. Created automatically by a signal.

| column   | type        | null | notes                                   |
|----------|-------------|------|-----------------------------------------|
| id       | bigint PK   | no   |                                         |
| user_id  | bigint FK   | no   | → auth_user, unique (one profile/user)  |
| role     | varchar     | no   | requester / agent / manager             |

## tickets_ticket
The central record. Almost everything hangs off this row.

| column        | type         | null | notes                                          |
|---------------|--------------|------|------------------------------------------------|
| id            | bigint PK    | no   |                                                |
| title         | varchar(200) | no   |                                                |
| description   | text         | no   |                                                |
| requester_id  | bigint FK    | no   | → auth_user (PROTECT)                           |
| assignee_id   | bigint FK    | yes  | → auth_user (SET NULL); null until assigned     |
| status        | varchar      | no   | open / assigned / escalated / resolved / closed |
| priority      | varchar      | no   | low / normal / high / urgent                    |
| category      | varchar(40)  | no   | free text, defaults to "other"                  |
| sla_due_at    | timestamptz  | yes  | deadline the escalation scan checks             |
| created_at    | timestamptz  | no   | auto                                            |
| updated_at    | timestamptz  | no   | auto                                            |
| escalated_at  | timestamptz  | yes  | stamped on escalate                             |
| resolved_at   | timestamptz  | yes  | stamped on resolve                              |
| closed_at     | timestamptz  | yes  | stamped on close                                |

Indexes: `status`, `assignee_id`, and `sla_due_at` — the columns the role-scoped
queues and the SLA sweep filter on.

## tickets_comment
The conversation thread on a ticket.

| column      | type        | null | notes                                  |
|-------------|-------------|------|----------------------------------------|
| id          | bigint PK   | no   |                                        |
| ticket_id   | bigint FK   | no   | → tickets_ticket (CASCADE)             |
| author_id   | bigint FK   | no   | → auth_user (CASCADE)                  |
| body        | text        | no   |                                        |
| is_internal | boolean     | no   | true = agent/manager only              |
| created_at  | timestamptz | no   |                                        |

## tickets_ticketevent
Append-only audit history. One row per status change. Never updated or deleted.

| column      | type        | null | notes                                     |
|-------------|-------------|------|-------------------------------------------|
| id          | bigint PK   | no   |                                           |
| ticket_id   | bigint FK   | no   | → tickets_ticket (CASCADE)                |
| actor_id    | bigint FK   | yes  | → auth_user (SET NULL); null = the system |
| from_status | varchar     | no   |                                           |
| to_status   | varchar     | no   |                                           |
| note        | text        | no   | reason / context (may be empty)           |
| created_at  | timestamptz | no   |                                           |

## Why the FK delete rules differ

- People FKs (`requester_id` PROTECT; `assignee_id`, `actor_id` SET NULL) — deleting a
  user must not erase ticket history.
- Child rows that only exist for a ticket (`comment`, `ticketevent`) CASCADE with it.
