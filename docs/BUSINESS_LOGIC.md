# deskflow — business logic

The rules that act on the tables in `DATABASE.md`. If the database is the nouns, this
is the verbs. Every rule below is enforced server-side and covered by a test — the UI
only decides which controls to render.

## Who can do what

| action                | requester           | agent               | manager |
|-----------------------|---------------------|---------------------|---------|
| open a ticket         | yes                 | yes                 | yes     |
| see a ticket          | own only            | assigned + queue    | all     |
| assign                | no                  | self-claim only     | anyone  |
| escalate (manual)     | no                  | no                  | yes     |
| resolve               | no                  | if assignee         | yes     |
| close                 | own (after resolve) | no                  | yes     |
| add internal comment  | no                  | yes                 | yes     |

The list endpoint enforces "see" by filtering the queryset — requester →
`requester_id = me`, agent → `assignee_id = me` plus the unassigned queue, manager →
everything — so out-of-scope objects 404 rather than 403. Each action endpoint then
checks its role rule and returns 403 with the reason.

## Ticket lifecycle

A ticket moves through `status` by these moves and no others:

| from      | action   | to        | also writes    |
|-----------|----------|-----------|----------------|
| open      | assign   | assigned  | `assignee_id`  |
| open      | escalate | escalated | `escalated_at` |
| assigned  | resolve  | resolved  | `resolved_at`  |
| assigned  | escalate | escalated | `escalated_at` |
| escalated | resolve  | resolved  | `resolved_at`  |
| resolved  | close    | closed    | `closed_at`    |

Rules:
- Anything not in this table is rejected (e.g. open → closed) with a 400.
- `closed` is terminal.
- Each transition is one model method funneled through a single chokepoint that locks
  the ticket row (`SELECT … FOR UPDATE`), re-checks the current status, writes the new
  status **and the audit row in one transaction** — so concurrent transitions
  serialize instead of double-firing, and status and audit can never disagree.

## Audit logging

Every transition inserts one `ticketevent` (`from_status`, `to_status`, `actor_id`,
optional `note`). `actor_id` is null when a background job made the change. Rows are
append-only — the table is the permanent record of who did what and when.

## SLA and escalation

- Each priority maps to an SLA window: urgent 4h, high 8h, normal 24h, low 72h.
- On create, `sla_due_at = now + window(priority)`.
- A breach = `sla_due_at < now()` while status is still `open` or `assigned`.
- Escalation has two triggers, both calling the same `escalate` method:
  - a manager does it by hand (with an optional note), or
  - the Celery beat job (every 5 minutes) finds breached tickets and escalates them
    with a null actor and an `sla breach` note.

## Auto-close

A resolved ticket the requester never confirms shouldn't sit forever. An hourly job
closes tickets in `resolved` whose `resolved_at` is older than the 3-day grace period,
with a null actor — the audit row shows the system closed it.

## Comment visibility

`is_internal = true` comments are staff-only in both directions: requesters can't
post them (403) and never receive them from `GET …/comments/`. Enforced server-side,
not by hiding UI.

## Invariants worth protecting

- An `open` ticket has no `assignee_id`; an unresolved ticket has no `resolved_at`.
- You can't resolve a ticket you aren't assigned to (unless manager).
- Status only changes through the transition methods — the field is read-only in the
  serializer, so a raw `PATCH status=…` is silently ignored.
