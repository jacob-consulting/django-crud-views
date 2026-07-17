import hashlib

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from resources import views as resources_views


def md5(key: str) -> str:
    return hashlib.md5(key.encode()).hexdigest()


class ResourcesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.viewer = User.objects.create_user(username="viewer", password="pw")
        cls.viewer.user_permissions.add(Permission.objects.get(codename="view_s3file"))
        cls.deleter = User.objects.create_user(username="deleter", password="pw")
        cls.deleter.user_permissions.add(
            Permission.objects.get(codename="view_s3file"),
            Permission.objects.get(codename="delete_s3file"),
        )

    def setUp(self):
        # the fake bucket is module state — reset it per test
        resources_views.FAKE_BUCKET[:] = [dict(row) for row in resources_views.INITIAL_BUCKET]


class S3ListTest(ResourcesTestCase):
    def test_list_renders_bucket_with_snippets(self):
        self.client.force_login(self.viewer)
        resp = self.client.get(reverse("s3file-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "reports/2026/q1.pdf")
        self.assertContains(resp, "snippet-panels")

    def test_list_requires_permission(self):
        user = get_user_model().objects.create_user(username="nobody", password="pw")
        self.client.force_login(user)
        resp = self.client.get(reverse("s3file-list"))
        self.assertEqual(resp.status_code, 403)


class S3DetailTest(ResourcesTestCase):
    def test_detail_renders_object(self):
        self.client.force_login(self.viewer)
        resp = self.client.get(reverse("s3file-detail", kwargs={"pk": md5("images/logo.png")}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "images/logo.png")


class S3DeleteTest(ResourcesTestCase):
    def test_delete_removes_item(self):
        self.client.force_login(self.deleter)
        resp = self.client.post(reverse("s3file-delete", kwargs={"pk": md5("images/logo.png")}), {"confirm": True})
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(any(row["key"] == "images/logo.png" for row in resources_views.FAKE_BUCKET))

    def test_delete_requires_delete_permission(self):
        self.client.force_login(self.viewer)
        resp = self.client.post(reverse("s3file-delete", kwargs={"pk": md5("images/logo.png")}))
        self.assertEqual(resp.status_code, 403)
