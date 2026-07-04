from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from tickets.models import Ticket

User = get_user_model()


def make_user(username, role):
    user = User.objects.create_user(username, password="x")
    user.profile.role = role
    user.profile.save()
    return user


class RoleRuleTests(APITestCase):
    """The 'who can do what' table from the business rules, enforced server-side."""

    def setUp(self):
        self.requester = make_user("req", "requester")
        self.agent = make_user("agent", "agent")
        self.other_agent = make_user("agent2", "agent")
        self.manager = make_user("boss", "manager")

    def make(self, status="open", assignee=None, requester=None):
        return Ticket.objects.create(
            title="t",
            description="d",
            requester=requester or self.requester,
            status=status,
            assignee=assignee,
        )

    # assign
    def test_requester_cannot_assign_own_ticket(self):
        ticket = self.make()
        self.client.force_authenticate(self.requester)
        r = self.client.post(f"/api/v1/tickets/{ticket.id}/assign/", {"assignee": self.agent.id})
        self.assertEqual(r.status_code, 403)

    def test_agent_can_self_claim_from_queue(self):
        ticket = self.make()
        self.client.force_authenticate(self.agent)
        r = self.client.post(f"/api/v1/tickets/{ticket.id}/assign/", {"assignee": self.agent.id})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["assignee"], self.agent.id)

    def test_agent_cannot_assign_to_someone_else(self):
        ticket = self.make()
        self.client.force_authenticate(self.agent)
        r = self.client.post(
            f"/api/v1/tickets/{ticket.id}/assign/", {"assignee": self.other_agent.id}
        )
        self.assertEqual(r.status_code, 403)

    # escalate
    def test_requester_cannot_escalate(self):
        ticket = self.make()
        self.client.force_authenticate(self.requester)
        r = self.client.post(f"/api/v1/tickets/{ticket.id}/escalate/")
        self.assertEqual(r.status_code, 403)

    def test_agent_cannot_escalate(self):
        ticket = self.make(status="assigned", assignee=self.agent)
        self.client.force_authenticate(self.agent)
        r = self.client.post(f"/api/v1/tickets/{ticket.id}/escalate/")
        self.assertEqual(r.status_code, 403)

    def test_manager_can_escalate(self):
        ticket = self.make()
        self.client.force_authenticate(self.manager)
        r = self.client.post(f"/api/v1/tickets/{ticket.id}/escalate/", {"note": "vip"})
        self.assertEqual(r.status_code, 200)

    # resolve
    def test_requester_cannot_resolve(self):
        ticket = self.make(status="assigned", assignee=self.agent)
        self.client.force_authenticate(self.requester)
        r = self.client.post(f"/api/v1/tickets/{ticket.id}/resolve/")
        self.assertEqual(r.status_code, 403)

    def test_assigned_agent_can_resolve(self):
        ticket = self.make(status="assigned", assignee=self.agent)
        self.client.force_authenticate(self.agent)
        r = self.client.post(f"/api/v1/tickets/{ticket.id}/resolve/")
        self.assertEqual(r.status_code, 200)

    def test_other_agents_ticket_is_invisible(self):
        ticket = self.make(status="assigned", assignee=self.other_agent)
        self.client.force_authenticate(self.agent)
        r = self.client.post(f"/api/v1/tickets/{ticket.id}/resolve/")
        self.assertEqual(r.status_code, 404)  # outside the agent's queryset

    # close
    def test_agent_cannot_close(self):
        ticket = self.make(status="resolved", assignee=self.agent)
        self.client.force_authenticate(self.agent)
        r = self.client.post(f"/api/v1/tickets/{ticket.id}/close/")
        self.assertEqual(r.status_code, 403)

    def test_requester_can_close_own_resolved_ticket(self):
        ticket = self.make(status="resolved")
        self.client.force_authenticate(self.requester)
        r = self.client.post(f"/api/v1/tickets/{ticket.id}/close/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "closed")

    # visibility
    def test_agent_can_open_queue_ticket_detail(self):
        ticket = self.make()  # unassigned
        self.client.force_authenticate(self.agent)
        r = self.client.get(f"/api/v1/tickets/{ticket.id}/")
        self.assertEqual(r.status_code, 200)

    # internal comments
    def test_requester_cannot_post_internal_comment(self):
        ticket = self.make()
        self.client.force_authenticate(self.requester)
        r = self.client.post(
            f"/api/v1/tickets/{ticket.id}/comments/", {"body": "sneaky", "is_internal": True}
        )
        self.assertEqual(r.status_code, 403)
        self.assertEqual(ticket.comments.count(), 0)

    def test_agent_can_post_internal_comment(self):
        ticket = self.make(status="assigned", assignee=self.agent)
        self.client.force_authenticate(self.agent)
        r = self.client.post(
            f"/api/v1/tickets/{ticket.id}/comments/", {"body": "note", "is_internal": True}
        )
        self.assertEqual(r.status_code, 201)
