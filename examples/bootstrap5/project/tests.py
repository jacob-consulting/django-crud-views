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


class SystemChecksTest(TestCase):
    def test_no_check_errors_with_every_viewset_registered(self):
        # `runserver` loads the full URLconf, which imports every feature app's
        # views.py and registers its ViewSets — so the crud_views ViewSet checks
        # run against all of them. Bare `manage.py check` does NOT import those
        # views.py modules, so it silently skips those checks and can pass while
        # `runserver` fails. Reproduce runserver's state here so this suite
        # catches ViewSet misconfiguration (e.g. a redirect-only action view
        # missing cv_backend_only) that a plain `check` would miss.
        from django.core import checks
        from django.urls import get_resolver

        get_resolver().url_patterns  # import every app's views.py via the URLconf
        errors = [e for e in checks.run_checks() if e.level >= checks.ERROR]
        self.assertEqual(errors, [], msg="\n".join(f"{e.id}: {e.msg}" for e in errors))


class FeatureRegistryTest(TestCase):
    def test_every_feature_declares_about_and_look_at(self):
        from project.features import FEATURES

        for feature in FEATURES:
            self.assertTrue(feature.about.strip(), f"{feature.app} has no about text")
            self.assertTrue(feature.look_at.strip(), f"{feature.app} has no look_at text")


class ExampleAboutTest(TestCase):
    def setUp(self):
        admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")
        self.client.force_login(admin)

    def test_every_feature_page_shows_about(self):
        from django.utils.html import escape

        for feature in FEATURES:
            resp = self.client.get(reverse(feature.url_name))
            self.assertContains(resp, 'id="example-about"', msg_prefix=feature.app)
            # a distinctive slice of the prose actually reaches the page.
            # escape() because Django autoescapes the rendered {{ feature.about }}
            # (e.g. an apostrophe becomes &#x27;), so the raw substring would not match.
            self.assertContains(resp, escape(feature.about[:40]), msg_prefix=feature.app)

    def test_example_about_empty_for_non_feature_view(self):
        from project.templatetags.example_tags import example_about
        from project.views import HomeView

        result = example_about({"view": HomeView()})
        self.assertIsNone(result["feature"])


class LookAtTest(TestCase):
    def test_look_at_appears_with_the_code_panel(self):
        from django.utils.html import escape

        admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")
        self.client.force_login(admin)
        feature = next(f for f in FEATURES if f.app == "polymorphic_demo")
        resp = self.client.get(reverse(feature.url_name))
        self.assertContains(resp, "Look at:")
        # escape() because {{ look_at }} is autoescaped in the rendered panel
        self.assertContains(resp, escape(feature.look_at[:40]))


class BreadcrumbAdoptionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="bc-admin", password="pw")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_every_feature_landing_page_shows_breadcrumb(self):
        for feature in FEATURES:
            with self.subTest(app=feature.app):
                resp = self.client.get(reverse(feature.url_name))
                self.assertEqual(resp.status_code, 200)
                self.assertContains(resp, 'aria-label="breadcrumb"')
                self.assertContains(resp, "Home")  # global prefix from settings
