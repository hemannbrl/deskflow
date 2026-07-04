from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class MeTests(APITestCase):
    def test_returns_username_and_role(self):
        user = User.objects.create_user("joe", password="x")
        user.profile.role = "agent"
        user.profile.save()

        self.client.force_authenticate(user)
        r = self.client.get("/api/v1/me/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["username"], "joe")
        self.assertEqual(r.data["role"], "agent")

    def test_anonymous_is_rejected(self):
        r = self.client.get("/api/v1/me/")
        self.assertEqual(r.status_code, 401)
