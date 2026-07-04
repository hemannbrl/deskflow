from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from tickets.models import Ticket

User = get_user_model()


def make_user(username, role):
    user = User.objects.create_user(username, password="x")
    user.profile.role = role
    user.profile.save()
    return user


class IllegalMoveTests(APITestCase):
    def setUp(self):
        self.manager = make_user("m", "manager")
        self.client.force_authenticate(self.manager)

    def test_closing_open_ticket_returns_400(self):
        ticket = Ticket.objects.create(title="t", description="d", requester=self.manager)
        r = self.client.post(f"/api/v1/tickets/{ticket.id}/close/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("cannot go open -> closed", r.data["detail"])

    def test_resolving_open_ticket_returns_400(self):
        ticket = Ticket.objects.create(title="t", description="d", requester=self.manager)
        r = self.client.post(f"/api/v1/tickets/{ticket.id}/resolve/")
        self.assertEqual(r.status_code, 400)

    def test_assign_without_assignee_returns_400(self):
        ticket = Ticket.objects.create(title="t", description="d", requester=self.manager)
        r = self.client.post(f"/api/v1/tickets/{ticket.id}/assign/", {})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data["detail"], "assignee is required")


class RoleVisibilityTests(APITestCase):
    def setUp(self):
        self.requester = make_user("req", "requester")
        self.agent = make_user("agent", "agent")
        self.other_agent = make_user("agent2", "agent")
        self.manager = make_user("boss", "manager")

        self.unassigned = Ticket.objects.create(
            title="unassigned", description="d", requester=self.requester
        )
        self.mine = Ticket.objects.create(
            title="mine",
            description="d",
            requester=self.requester,
            status="assigned",
            assignee=self.agent,
        )
        self.someone_elses = Ticket.objects.create(
            title="someone elses",
            description="d",
            requester=self.requester,
            status="assigned",
            assignee=self.other_agent,
        )

    def titles(self):
        r = self.client.get("/api/v1/tickets/")
        return {t["title"] for t in r.data["results"]}

    def test_agent_sees_assigned_and_unassigned_queue(self):
        self.client.force_authenticate(self.agent)
        self.assertEqual(self.titles(), {"unassigned", "mine"})

    def test_manager_sees_everything(self):
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.titles(), {"unassigned", "mine", "someone elses"})

    def test_agent_cannot_open_someone_elses_ticket(self):
        self.client.force_authenticate(self.agent)
        r = self.client.get(f"/api/v1/tickets/{self.someone_elses.id}/")
        self.assertEqual(r.status_code, 404)
