from datetime import timedelta

from django.utils import timezone

from .models import SlaPolicy, Ticket

WINDOWS = {"urgent": 4, "high": 8, "normal": 24, "low": 72}  # default hours


def window_hours(priority):
    """The SLA window for a priority: a manager-set SlaPolicy row if one
    exists, else the built-in default."""
    policy = SlaPolicy.objects.filter(priority=priority).values_list("hours", flat=True).first()
    return policy if policy is not None else WINDOWS[priority]


def due_at(priority, start=None):
    start = start or timezone.now()
    return start + timedelta(hours=window_hours(priority))


def escalate_breached(now=None):
    now = now or timezone.now()
    breached = Ticket.objects.filter(sla_due_at__lt=now, status__in=["open", "assigned"])
    count = 0
    for ticket in breached:
        ticket.escalate(actor=None, note="sla breach")
        count += 1
    return count
