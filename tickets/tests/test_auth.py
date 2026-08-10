from django.core.cache import cache
from rest_framework.test import APITestCase


class AuthTests(APITestCase):
    def setUp(self):
        # Reset the 'auth' scope throttle counter (10/min) between tests so a run's
        # cumulative auth calls don't trip it.
        cache.clear()

    def _register_and_token(self, username):
        self.client.post("/api/auth/register/", {"username": username, "password": "secret123"})
        r = self.client.post("/api/auth/token/", {"username": username, "password": "secret123"})
        self.assertEqual(r.status_code, 200)
        return r.data

    def test_register_then_get_token(self):
        r = self.client.post("/api/auth/register/", {"username": "joe", "password": "secret123"})
        self.assertEqual(r.status_code, 201)

        r = self.client.post("/api/auth/token/", {"username": "joe", "password": "secret123"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)

    def test_refresh_rotates_and_blacklists_old_token(self):
        old_refresh = self._register_and_token("roe")["refresh"]
        rotated = self.client.post("/api/auth/token/refresh/", {"refresh": old_refresh})
        self.assertEqual(rotated.status_code, 200)
        self.assertIn("refresh", rotated.data)  # rotation issues a new refresh
        # The old refresh is now blacklisted and can't mint another access token.
        reuse = self.client.post("/api/auth/token/refresh/", {"refresh": old_refresh})
        self.assertEqual(reuse.status_code, 401)

    def test_logout_blacklists_refresh_token(self):
        refresh = self._register_and_token("kay")["refresh"]
        out = self.client.post("/api/auth/logout/", {"refresh": refresh})
        self.assertEqual(out.status_code, 200)
        again = self.client.post("/api/auth/token/refresh/", {"refresh": refresh})
        self.assertEqual(again.status_code, 401)
