from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

import crud_views
from project.features import FEATURES


class FooterTest(TestCase):
    LINKS = (
        "https://django-crud-views.readthedocs.io/",
        "https://github.com/jacob-consulting/django-crud-views",
        "https://django-crud-views-demo.onrender.com/",
    )

    def assert_footer(self, resp):
        self.assertContains(resp, 'id="site-footer"')
        self.assertContains(resp, f"django-crud-views {crud_views.__version__}")
        for url in self.LINKS:
            self.assertContains(resp, f'href="{url}"')

    def test_footer_on_home_and_login(self):
        for name in ("home", "login"):
            self.assert_footer(self.client.get(reverse(name)))

    @override_settings(DEMO_MODE=True)
    def test_footer_on_demo(self):
        self.assert_footer(self.client.get(reverse("login")))


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

    def test_pages_do_not_advertise_admin_user(self):
        for name in ("home", "login"):
            resp = self.client.get(reverse(name))
            self.assertNotContains(resp, "admin/admin")
            self.assertContains(resp, "alice/alice")
            self.assertContains(resp, "bob/bob")


class SeedCommandTest(TestCase):
    def test_seed_twice_is_idempotent(self):
        call_command("seed")
        call_command("seed")
        User = get_user_model()
        self.assertTrue(User.objects.filter(username="alice", is_superuser=False).exists())
        self.assertTrue(User.objects.filter(username="bob", is_superuser=False).exists())

    def test_seed_creates_no_admin_user(self):
        call_command("seed")
        User = get_user_model()
        self.assertFalse(User.objects.filter(username="admin").exists())
        self.assertFalse(User.objects.filter(is_superuser=True).exists())


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

        # accessing url_patterns imports every app's views.py via the URLconf; assert non-empty so a
        # broken URLconf (e.g. an import error swallowed upstream) fails loudly here instead of silently
        # skipping the check below
        assert get_resolver().url_patterns, "URLconf resolved no patterns"
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


class DocRefTest(SimpleTestCase):
    def test_url_plain_page(self):
        from project.features import DOCS_BASE, DocRef

        ref = DocRef(page="reference/nested.md", label="Nested")
        self.assertEqual(ref.url, f"{DOCS_BASE}/reference/nested/")

    def test_url_with_anchor(self):
        from project.features import DOCS_BASE, DocRef

        ref = DocRef(page="reference/nested.md", label="Nested", anchor="creating-children")
        self.assertEqual(ref.url, f"{DOCS_BASE}/reference/nested/#creating-children")

    def test_url_index_pages(self):
        from project.features import DOCS_BASE, DocRef

        self.assertEqual(DocRef(page="getting_started/index.md", label="x").url, f"{DOCS_BASE}/getting_started/")
        self.assertEqual(DocRef(page="index.md", label="x").url, f"{DOCS_BASE}/")

    def test_docs_base_is_stable(self):
        from project.features import DOCS_BASE

        self.assertEqual(DOCS_BASE, "https://django-crud-views.readthedocs.io/en/stable")

    def test_feature_docs_defaults_to_empty_tuple(self):
        from project.features import Feature

        feature = Feature(
            app="x", title="X", description="d", about="a", look_at="l", url_name="home", icon="fa-solid fa-x"
        )
        self.assertEqual(feature.docs, ())


class DocRefsPanelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="docs-admin", password="pw")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_every_feature_page_lists_its_doc_refs(self):
        from django.utils.html import escape

        for feature in FEATURES:
            with self.subTest(app=feature.app):
                resp = self.client.get(reverse(feature.url_name))
                self.assertContains(resp, "References to documentation")
                for ref in feature.docs:
                    self.assertContains(resp, f'<a href="{ref.url}" target="_blank" rel="noopener">')
                    self.assertContains(resp, escape(ref.label))

    def test_heading_translated_de_labels_stay_english(self):
        from django.utils.html import escape

        feature = next(f for f in FEATURES if f.app == "nested")
        resp = self.client.get(reverse(feature.url_name), HTTP_ACCEPT_LANGUAGE="de")
        self.assertContains(resp, "Verweise auf die Dokumentation")
        self.assertNotContains(resp, "References to documentation")
        self.assertContains(resp, escape(feature.docs[1].label))
        self.assertContains(resp, f'href="{feature.docs[1].url}"')

    def test_docs_empty_for_non_feature_view(self):
        from project.templatetags.example_tags import snippet_panels
        from project.views import HomeView

        self.assertEqual(snippet_panels({"view": HomeView()})["docs"], ())

    def test_home_has_no_doc_refs_heading(self):
        resp = self.client.get(reverse("home"))
        self.assertNotContains(resp, "References to documentation")

    def test_no_heading_when_docs_empty(self):
        from django.template.loader import render_to_string

        html = render_to_string(
            "project/snippet_panels.html",
            {"panels": [{"id": "p", "title": "t", "html": "h"}], "look_at": "", "docs": ()},
        )
        self.assertIn("snippet-panels", html)
        self.assertNotIn("References to documentation", html)
        self.assertNotIn("<ul", html)
