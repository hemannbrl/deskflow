from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from tickets.models import SlaPolicy
from tickets.sla import due_at, window_hours

User = get_user_model()


class SlaPolicyTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user("m", password="x")
        self.manager.profile.role = "manager"
        self.manager.profile.save()
        self.agent = User.objects.create_user("a", password="x")
        self.agent.profile.role = "agent"
        self.agent.profile.save()
        self.requester = User.objects.create_user("r", password="x")

    def test_window_falls_back_to_default(self):
        self.assertEqual(window_hours("urgent"), 4)

    def test_policy_overrides_default(self):
        SlaPolicy.objects.create(priority="urgent", hours=2)
        self.assertEqual(window_hours("urgent"), 2)
        start = timezone.now()
        self.assertEqual(due_at("urgent", start=start), start + timedelta(hours=2))

    def test_new_ticket_uses_policy_window(self):
        SlaPolicy.objects.create(priority="high", hours=1)
        self.client.force_authenticate(self.requester)
        r = self.client.post(
            "/api/v1/tickets/", {"title": "t", "description": "d", "priority": "high"}
        )
        self.assertEqual(r.status_code, 201)
        created = timezone.now()
        due = timezone.datetime.fromisoformat(r.data["sla_due_at"].replace("Z", "+00:00"))
        self.assertLess(abs((due - created).total_seconds() - 3600), 60)

    def test_manager_can_set_policy_via_api(self):
        self.client.force_authenticate(self.manager)
        r = self.client.post("/api/v1/sla-policies/", {"priority": "low", "hours": 48})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["updated_by"], self.manager.id)
        self.assertEqual(window_hours("low"), 48)

    def test_zero_hour_window_rejected(self):
        self.client.force_authenticate(self.manager)
        r = self.client.post("/api/v1/sla-policies/", {"priority": "low", "hours": 0})
        self.assertEqual(r.status_code, 400)

    def test_agent_reads_but_cannot_write(self):
        SlaPolicy.objects.create(priority="normal", hours=12)
        self.client.force_authenticate(self.agent)
        r = self.client.get("/api/v1/sla-policies/")
        self.assertEqual(r.status_code, 200)
        r = self.client.post("/api/v1/sla-policies/", {"priority": "low", "hours": 48})
        self.assertEqual(r.status_code, 403)

    def test_requester_gets_403(self):
        self.client.force_authenticate(self.requester)
        r = self.client.get("/api/v1/sla-policies/")
        self.assertEqual(r.status_code, 403)

    def test_duplicate_priority_rejected(self):
        SlaPolicy.objects.create(priority="low", hours=48)
        self.client.force_authenticate(self.manager)
        r = self.client.post("/api/v1/sla-policies/", {"priority": "low", "hours": 24})
        self.assertEqual(r.status_code, 400)
