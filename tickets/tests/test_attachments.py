import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from tickets.models import Ticket

User = get_user_model()

TEMP_MEDIA = tempfile.mkdtemp(prefix="deskflow-test-media-")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class AttachmentTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.requester = User.objects.create_user("r", password="x")
        self.stranger = User.objects.create_user("s", password="x")
        self.ticket = Ticket.objects.create(title="t", description="d", requester=self.requester)
        self.url = f"/api/v1/tickets/{self.ticket.id}/attachments/"

    def _upload(self, name="shot.png", content=b"fake-png-bytes"):
        return self.client.post(
            self.url, {"file": SimpleUploadedFile(name, content)}, format="multipart"
        )

    def test_requester_can_upload_and_list(self):
        self.client.force_authenticate(self.requester)
        r = self._upload()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["original_name"], "shot.png")
        self.assertEqual(r.data["size"], len(b"fake-png-bytes"))
        self.assertNotIn("file", r.data)  # storage path never exposed
        r = self.client.get(self.url)
        self.assertEqual(len(r.data), 1)

    def test_disallowed_extension_rejected(self):
        self.client.force_authenticate(self.requester)
        r = self._upload(name="malware.exe")
        self.assertEqual(r.status_code, 400)

    def test_oversized_file_rejected(self):
        self.client.force_authenticate(self.requester)
        r = self._upload(name="big.png", content=b"x" * (5 * 1024 * 1024 + 1))
        self.assertEqual(r.status_code, 400)

    def test_stranger_cannot_see_or_upload(self):
        self.client.force_authenticate(self.requester)
        self._upload()
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self._upload().status_code, 404)

    def test_download_streams_file_with_permission_check(self):
        self.client.force_authenticate(self.requester)
        attachment_id = self._upload(content=b"the-bytes").data["id"]
        download_url = f"{self.url}{attachment_id}/download/"

        r = self.client.get(download_url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(b"".join(r.streaming_content), b"the-bytes")

        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.client.get(download_url).status_code, 404)
