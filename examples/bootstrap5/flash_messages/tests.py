from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from lxml import html as lxml_html
from project.seeding import grant_model_perms

from flash_messages.models import Notice

# messages.md "Levels": the class each Django level renders with
LEVEL_CLASSES = {"info": "alert-info", "success": "alert-success", "warning": "alert-warning", "error": "alert-danger"}


class FlashMessagesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="flash-test", password="pw")
        grant_model_perms(cls.user, Notice, actions=("view",))

    def setUp(self):
        self.client.force_login(self.user)

    @staticmethod
    def url():
        return reverse("notice-compose")

    def alerts(self, resp):
        return lxml_html.fromstring(resp.content).xpath("//*[@role='alert']")


class ComposePageTest(FlashMessagesTestCase):
    def test_page_renders_form(self):
        resp = self.client.get(self.url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'name="level"')
        self.assertContains(resp, 'name="text"')

    def test_page_renders_one_inline_cv_alert(self):
        (alert,) = self.alerts(self.client.get(self.url()))
        self.assertIn("alert-info", alert.get("class"))
        self.assertNotIn("alert-dismissible", alert.get("class"))  # cv_alert default: not dismissible
        self.assertIn("cv_alert", alert.text_content())

    def test_user_without_view_permission_is_refused(self):
        self.client.force_login(get_user_model().objects.create_user(username="flash-nobody", password="pw"))
        self.assertEqual(self.client.get(self.url()).status_code, 403)


class SendMessageTest(FlashMessagesTestCase):
    def send(self, level, text):
        return self.client.post(self.url(), {"level": level, "text": text}, follow=True)

    def test_each_level_renders_its_alert_class(self):
        for level, css in LEVEL_CLASSES.items():
            with self.subTest(level=level):
                resp = self.send(level, f"Hello at {level}")
                self.assertEqual(resp.redirect_chain, [(self.url(), 302)])
                (alert,) = [a for a in self.alerts(resp) if f"Hello at {level}" in a.text_content()]
                self.assertIn(f"alert {css}", alert.get("class"))
                self.assertIn("alert-dismissible", alert.get("class"))

    def test_debug_is_below_the_default_message_level(self):
        resp = self.send("debug", "Hello at debug")
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "Hello at debug")

    def test_missing_text_rerenders_with_error(self):
        resp = self.client.post(self.url(), {"level": "info", "text": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["form"].errors["text"])

    def test_unknown_level_is_rejected(self):
        resp = self.client.post(self.url(), {"level": "shout", "text": "x"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["form"].errors["level"])


class SeedTest(TestCase):
    def test_seed_grants_view_to_demo_users(self):
        call_command("seed")
        call_command("seed")
        for username in ("alice", "bob"):
            self.assertTrue(get_user_model().objects.get(username=username).has_perm("flash_messages.view_notice"))
