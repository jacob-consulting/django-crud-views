from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from project.features import FEATURES


class HomePageTest(TestCase):
    def test_home_page_renders_anonymously(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "django-crud-views")

    def test_home_page_links_every_feature(self):
        resp = self.client.get(reverse("home"))
        for feature in FEATURES:
            self.assertContains(resp, reverse(feature.url_name))

    def test_every_feature_landing_page_renders(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username="test-admin", password="pw")
        self.client.force_login(admin)
        for feature in FEATURES:
            resp = self.client.get(reverse(feature.url_name))
            self.assertEqual(resp.status_code, 200, f"landing page of {feature.app} broke")

    def test_login_page_shows_demo_credentials(self):
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "alice")


class SeedCommandTest(TestCase):
    def test_seed_twice_is_idempotent(self):
        call_command("seed")
        call_command("seed")
        User = get_user_model()
        self.assertTrue(User.objects.filter(username="admin", is_superuser=True).exists())
        self.assertTrue(User.objects.filter(username="alice", is_superuser=False).exists())
        self.assertTrue(User.objects.filter(username="bob", is_superuser=False).exists())


class SnippetPanelsTest(TestCase):
    def test_highlight_produces_html(self):
        from project.templatetags.example_tags import _highlight

        html = _highlight("def foo():\n    return 1\n")
        self.assertIn("<span", html)
        self.assertIn("foo", html)

    def test_snippet_panels_empty_for_non_feature_view(self):
        from project.templatetags.example_tags import snippet_panels
        from project.views import HomeView

        result = snippet_panels({"view": HomeView()})
        self.assertEqual(result["panels"], [])
