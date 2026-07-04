from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from tickets.models import Ticket
from tickets.tasks import auto_close_resolved

User = get_user_model()


class AutoCloseTests(TestCase):
    def test_stale_resolved_ticket_is_closed(self):
        user = User.objects.create_user("r", password="x")
        ticket = Ticket.objects.create(
            title="t",
            description="d",
            requester=user,
            status="resolved",
            resolved_at=timezone.now() - timedelta(days=5),
        )
        self.assertEqual(auto_close_resolved(grace_days=3), 1)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "closed")
