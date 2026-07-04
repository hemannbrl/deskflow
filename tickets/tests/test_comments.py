from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from tickets.models import Comment, Ticket

User = get_user_model()


class CommentVisibilityTests(APITestCase):
    def test_requester_does_not_see_internal_notes(self):
        requester = User.objects.create_user("req", password="x")
        ticket = Ticket.objects.create(title="t", description="d", requester=requester)
        Comment.objects.create(ticket=ticket, author=requester, body="public")
        Comment.objects.create(ticket=ticket, author=requester, body="hidden", is_internal=True)

        self.client.force_authenticate(requester)
        r = self.client.get(f"/api/tickets/{ticket.id}/comments/")
        bodies = [c["body"] for c in r.data]
        self.assertIn("public", bodies)
        self.assertNotIn("hidden", bodies)
