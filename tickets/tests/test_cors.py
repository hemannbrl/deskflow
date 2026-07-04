from django.test import override_settings
from rest_framework.test import APITestCase


class CorsTests(APITestCase):
    @override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:3000"])
    def test_preflight_allows_frontend_origin(self):
        r = self.client.options(
            "/api/auth/token/",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )
        self.assertEqual(r["access-control-allow-origin"], "http://localhost:3000")

    @override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:3000"])
    def test_unknown_origin_is_not_allowed(self):
        r = self.client.options(
            "/api/auth/token/",
            HTTP_ORIGIN="http://evil.example",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )
        self.assertNotIn("access-control-allow-origin", r)
