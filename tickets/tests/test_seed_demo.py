from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from tickets.models import Comment, Ticket, TicketEvent

User = get_user_model()


def seed():
    call_command("seed_demo", stdout=StringIO())


class SeedDemoTests(TestCase):
    def test_seeds_users_and_tickets_in_every_state(self):
        seed()

        self.assertEqual(Ticket.objects.count(), 26)
        statuses = set(Ticket.objects.values_list("status", flat=True))
        self.assertEqual(statuses, {"open", "assigned", "escalated", "resolved", "closed"})

        agent = User.objects.get(username="demo_agent")
        self.assertEqual(agent.profile.role, "agent")
        self.assertTrue(agent.check_password("deskflow123"))

        # lifecycle walked through the real transitions -> genuine audit rows,
        # including system escalations from the simulated SLA job
        self.assertTrue(TicketEvent.objects.filter(actor__isnull=True, note="sla breach").exists())
        self.assertTrue(TicketEvent.objects.filter(to_status="closed").exists())
        self.assertTrue(Comment.objects.filter(is_internal=True).exists())

        # at least the two forced ones are past their SLA so the UI shows overdue state
        overdue = Ticket.objects.filter(status="open", sla_due_at__lt=timezone.now())
        self.assertGreaterEqual(overdue.count(), 2)

    def test_reseeding_wipes_and_recreates(self):
        seed()
        first_ids = set(Ticket.objects.values_list("id", flat=True))
        seed()
        self.assertEqual(Ticket.objects.count(), 26)
        self.assertFalse(first_ids & set(Ticket.objects.values_list("id", flat=True)))
