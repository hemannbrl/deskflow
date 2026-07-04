from django.contrib.auth import get_user_model
from django.test import TestCase

from tickets.models import Ticket, TransitionError

User = get_user_model()


class TransitionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("agent", password="x")

    def make(self, status="open"):
        return Ticket.objects.create(title="t", description="d", requester=self.user, status=status)

    def test_cannot_close_open_ticket(self):
        with self.assertRaises(TransitionError):
            self.make("open").close()

    def test_resolve_stamps_and_logs(self):
        t = self.make("assigned")
        t.resolve(actor=self.user)
        self.assertEqual(t.status, "resolved")
        self.assertIsNotNone(t.resolved_at)
        self.assertEqual(t.events.last().to_status, "resolved")

    def test_assign_sets_assignee_and_logs(self):
        t = self.make("open")
        t.assign(self.user, actor=self.user)
        self.assertEqual(t.status, "assigned")
        self.assertEqual(t.assignee, self.user)
