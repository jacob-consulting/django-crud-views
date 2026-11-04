from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from project.features import DocRef


class ThemePageTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="theming-user", password="pw")

    def setUp(self):
        self.client.force_login(self.user)

    def get(self):
        resp = self.client.get(reverse("theming-index"))
        self.assertEqual(resp.status_code, 200)
        return resp

    def test_anonymous_is_redirected_to_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("theming-index")).status_code, 302)

    def test_links_to_the_reference_pages(self):
        resp = self.get()
        for page in ("reference/theme.md", "reference/templates.md", "reference/buttons.md", "reference/icons.md"):
            self.assertContains(resp, DocRef(page=page, label="x").url, msg_prefix=page)

    def test_without_demo_url_shows_coming_soon(self):
        resp = self.get()
        self.assertContains(resp, 'id="tabler-demo-coming-soon"')
        self.assertContains(resp, "coming soon")
        self.assertNotContains(resp, "onrender.com/tabler")
        # the site's own demo chrome may link onrender.com; the placeholder must not add a link
        self.assertNotContains(resp, 'id="tabler-demo-link"')

    def test_with_demo_url_links_to_it(self):
        with mock.patch("theming.views.TABLER_DEMO_URL", "https://example.onrender.com/"):
            resp = self.get()
        self.assertContains(resp, 'id="tabler-demo-link"')
        self.assertContains(resp, 'href="https://example.onrender.com/"')
        self.assertNotContains(resp, 'id="tabler-demo-coming-soon"')

    def test_feature_chrome(self):
        resp = self.get()
        self.assertContains(resp, 'id="example-about"')
        self.assertContains(resp, 'id="snippet-panels"')
        self.assertContains(resp, 'aria-label="breadcrumb"')
