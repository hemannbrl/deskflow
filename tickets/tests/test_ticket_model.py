from django.contrib.auth import get_user_model
from django.test import TestCase

from tickets.models import Ticket

User = get_user_model()


class TicketModelTests(TestCase):
    def test_new_ticket_defaults_to_open_unassigned(self):
        user = User.objects.create_user("r", password="x")
        t = Ticket.objects.create(title="t", description="d", requester=user)
        self.assertEqual(t.status, "open")
        self.assertIsNone(t.assignee)
