from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from tickets.models import CannedResponse

User = get_user_model()


class CannedResponseTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user("m", password="x")
        self.manager.profile.role = "manager"
        self.manager.profile.save()
        self.agent = User.objects.create_user("a", password="x")
        self.agent.profile.role = "agent"
        self.agent.profile.save()
        self.requester = User.objects.create_user("r", password="x")
        self.template = CannedResponse.objects.create(
            title="Password reset", body="Use the forgot-password link.", created_by=self.manager
        )

    def test_manager_can_create(self):
        self.client.force_authenticate(self.manager)
        r = self.client.post(
            "/api/v1/canned-responses/", {"title": "Greeting", "body": "Hi, thanks for writing in."}
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["created_by"], self.manager.id)

    def test_agent_can_read_but_not_write(self):
        self.client.force_authenticate(self.agent)
        r = self.client.get("/api/v1/canned-responses/")
        self.assertEqual(r.status_code, 200)
        titles = [row["title"] for row in (r.data["results"] if "results" in r.data else r.data)]
        self.assertIn("Password reset", titles)
        r = self.client.post("/api/v1/canned-responses/", {"title": "x", "body": "y"})
        self.assertEqual(r.status_code, 403)

    def test_requester_gets_403(self):
        self.client.force_authenticate(self.requester)
        r = self.client.get("/api/v1/canned-responses/")
        self.assertEqual(r.status_code, 403)

    def test_manager_can_update_and_delete(self):
        self.client.force_authenticate(self.manager)
        r = self.client.patch(
            f"/api/v1/canned-responses/{self.template.id}/", {"body": "Updated body."}
        )
        self.assertEqual(r.status_code, 200)
        self.template.refresh_from_db()
        self.assertEqual(self.template.body, "Updated body.")
        r = self.client.delete(f"/api/v1/canned-responses/{self.template.id}/")
        self.assertEqual(r.status_code, 204)
        self.assertFalse(CannedResponse.objects.filter(pk=self.template.pk).exists())

    def test_anonymous_gets_401(self):
        r = self.client.get("/api/v1/canned-responses/")
        self.assertEqual(r.status_code, 401)
