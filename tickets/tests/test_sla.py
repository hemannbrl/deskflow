from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from tickets.models import Ticket
from tickets.sla import due_at, escalate_breached

User = get_user_model()


class SlaTests(TestCase):
    def test_breached_ticket_is_escalated(self):
        user = User.objects.create_user("r", password="x")
        ticket = Ticket.objects.create(
            title="t",
            description="d",
            requester=user,
            status="open",
            sla_due_at=timezone.now() - timedelta(hours=1),
        )
        self.assertEqual(escalate_breached(), 1)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "escalated")
        self.assertEqual(ticket.events.get().note, "sla breach")

    def test_resolved_and_unbreached_tickets_are_left_alone(self):
        user = User.objects.create_user("r", password="x")
        Ticket.objects.create(
            title="resolved",
            description="d",
            requester=user,
            status="resolved",
            sla_due_at=timezone.now() - timedelta(hours=1),
        )
        Ticket.objects.create(
            title="not due yet",
            description="d",
            requester=user,
            status="open",
            sla_due_at=timezone.now() + timedelta(hours=1),
        )
        self.assertEqual(escalate_breached(), 0)

    def test_due_at_uses_priority_window(self):
        start = timezone.now()
        self.assertEqual(due_at("urgent", start), start + timedelta(hours=4))
        self.assertEqual(due_at("low", start), start + timedelta(hours=72))
