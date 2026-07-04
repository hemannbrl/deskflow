from datetime import timedelta

from django.utils import timezone

from .models import Ticket

WINDOWS = {"urgent": 4, "high": 8, "normal": 24, "low": 72}  # hours


def due_at(priority, start=None):
    start = start or timezone.now()
    return start + timedelta(hours=WINDOWS[priority])


def escalate_breached(now=None):
    now = now or timezone.now()
    breached = Ticket.objects.filter(sla_due_at__lt=now, status__in=["open", "assigned"])
    count = 0
    for ticket in breached:
        ticket.escalate(actor=None, note="sla breach")
        count += 1
    return count
