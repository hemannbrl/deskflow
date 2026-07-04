from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from tickets.models import Ticket

User = get_user_model()


class TicketScopeTests(APITestCase):
    def setUp(self):
        self.requester = User.objects.create_user("req", password="x")
        self.other = User.objects.create_user("other", password="x")

    def test_requester_sees_only_their_own(self):
        Ticket.objects.create(title="mine", description="d", requester=self.requester)
        Ticket.objects.create(title="theirs", description="d", requester=self.other)
        self.client.force_authenticate(self.requester)

        r = self.client.get("/api/tickets/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)
        self.assertEqual(r.data[0]["title"], "mine")
