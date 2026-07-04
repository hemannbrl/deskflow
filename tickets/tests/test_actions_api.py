from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from tickets.models import Ticket

User = get_user_model()


class TicketActionTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user("m", password="x")
        self.manager.profile.role = "manager"
        self.manager.profile.save()
        self.agent = User.objects.create_user("a", password="x")
        self.agent.profile.role = "agent"
        self.agent.profile.save()
        self.ticket = Ticket.objects.create(title="t", description="d", requester=self.manager)
        self.client.force_authenticate(self.manager)

    def test_assign_via_api(self):
        url = f"/api/v1/tickets/{self.ticket.id}/assign/"
        r = self.client.post(url, {"assignee": self.agent.id})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "assigned")
        self.assertEqual(r.data["assignee"], self.agent.id)

    def test_escalate_via_api_records_note(self):
        url = f"/api/v1/tickets/{self.ticket.id}/escalate/"
        r = self.client.post(url, {"note": "vip customer"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "escalated")
        self.assertEqual(self.ticket.events.get().note, "vip customer")

    def test_full_lifecycle_and_event_history(self):
        self.client.post(f"/api/v1/tickets/{self.ticket.id}/assign/", {"assignee": self.agent.id})
        self.client.post(f"/api/v1/tickets/{self.ticket.id}/resolve/")
        self.client.post(f"/api/v1/tickets/{self.ticket.id}/close/")

        r = self.client.get(f"/api/v1/tickets/{self.ticket.id}/events/")
        self.assertEqual(r.status_code, 200)
        moves = [(e["from_status"], e["to_status"]) for e in r.data]
        self.assertEqual(
            moves, [("open", "assigned"), ("assigned", "resolved"), ("resolved", "closed")]
        )

    def test_status_cannot_be_patched_directly(self):
        r = self.client.patch(f"/api/v1/tickets/{self.ticket.id}/", {"status": "closed"})
        self.assertEqual(r.status_code, 200)  # read-only field is silently ignored
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "open")
