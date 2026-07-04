from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from tickets.models import Ticket
from tickets.sla import escalate_breached

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
