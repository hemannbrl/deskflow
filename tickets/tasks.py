from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import Ticket
from .sla import escalate_breached


@shared_task
def run_sla_escalation():
    return escalate_breached()


@shared_task
def auto_close_resolved(grace_days=3):
    cutoff = timezone.now() - timedelta(days=grace_days)
    stale = Ticket.objects.filter(status="resolved", resolved_at__lt=cutoff)
    count = 0
    for ticket in stale:
        ticket.close(actor=None)
        count += 1
    return count
