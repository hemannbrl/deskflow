from django.contrib.auth import get_user_model
from django.test import TestCase

from tickets.models import Ticket, TransitionError

User = get_user_model()


class TransitionLockingTests(TestCase):
    """_transition must re-read status under a row lock, so a stale instance
    (another request, or the SLA job) can't repeat a transition."""

    def test_stale_instance_cannot_repeat_a_transition(self):
        user = User.objects.create_user("a", password="x")
        ticket = Ticket.objects.create(
            title="t", description="d", requester=user, status="assigned", assignee=user
        )
        stale = Ticket.objects.get(pk=ticket.pk)  # second copy, as a parallel request sees it

        ticket.resolve(actor=user)
        with self.assertRaises(TransitionError):
            stale.resolve(actor=user)  # in-memory status is still "assigned"

        self.assertEqual(ticket.events.count(), 1)  # exactly one audit row

    def test_event_records_the_db_status_not_the_stale_one(self):
        user = User.objects.create_user("b", password="x")
        ticket = Ticket.objects.create(title="t", description="d", requester=user)
        stale = Ticket.objects.get(pk=ticket.pk)

        ticket.assign(user, actor=user)  # db is now "assigned"
        stale.resolve(actor=user)  # stale thinks "open", but resolve is legal from db state

        event = stale.events.get(to_status="resolved")
        self.assertEqual(event.from_status, "assigned")
