from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from tickets.models import Comment, Ticket

User = get_user_model()


class UsernameFieldTests(APITestCase):
    def setUp(self):
        self.requester = User.objects.create_user("req", password="x")
        self.ticket = Ticket.objects.create(title="t", description="d", requester=self.requester)
        self.client.force_authenticate(self.requester)

    def test_ticket_carries_usernames(self):
        r = self.client.get(f"/api/v1/tickets/{self.ticket.id}/")
        self.assertEqual(r.data["requester_username"], "req")
        self.assertIsNone(r.data["assignee_username"])

    def test_event_actor_username_is_null_for_system(self):
        self.ticket.escalate(actor=None, note="sla breach")
        r = self.client.get(f"/api/v1/tickets/{self.ticket.id}/events/")
        self.assertIsNone(r.data[0]["actor_username"])

    def test_comment_carries_author_username(self):
        Comment.objects.create(ticket=self.ticket, author=self.requester, body="hi")
        r = self.client.get(f"/api/v1/tickets/{self.ticket.id}/comments/")
        self.assertEqual(r.data[0]["author_username"], "req")
