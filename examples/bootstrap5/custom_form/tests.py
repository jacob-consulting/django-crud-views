from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from custom_form.models import Contact


class CustomFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")
        cls.contact = Contact.objects.create(name="Ada", email="ada@example.com")

    def setUp(self):
        self.client.force_login(self.admin)

    def remind_url(self):
        return reverse("contact-remind", kwargs={"pk": self.contact.pk})


class RemindTest(CustomFormTestCase):
    def test_page_renders(self):
        resp = self.client.get(self.remind_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'name="note"')

    def test_post_sets_last_reminded_and_flashes(self):
        self.assertIsNone(self.contact.last_reminded_dt)
        resp = self.client.post(self.remind_url(), {"note": "Please reply"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.contact.refresh_from_db()
        self.assertIsNotNone(self.contact.last_reminded_dt)
        self.assertContains(resp, "Ada")
        self.assertEqual([str(m) for m in resp.context["messages"]], ["Reminded contact “Ada”"])

    def test_post_without_note_rerenders_with_error(self):
        resp = self.client.post(self.remind_url(), {"note": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["form"].errors["note"])
        self.contact.refresh_from_db()
        self.assertIsNone(self.contact.last_reminded_dt)


class InviteTest(CustomFormTestCase):
    def test_page_renders(self):
        resp = self.client.get(reverse("contact-invite"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'name="email"')

    def test_post_creates_contact(self):
        resp = self.client.post(reverse("contact-invite"), {"email": "grace@example.com"})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Contact.objects.filter(email="grace@example.com").exists())

    def test_post_invalid_email_creates_nothing(self):
        resp = self.client.post(reverse("contact-invite"), {"email": "nope"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Contact.objects.count(), 1)


class ListTest(CustomFormTestCase):
    def test_list_links_to_both_forms(self):
        resp = self.client.get(reverse("contact-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse("contact-invite"))
        self.assertContains(resp, self.remind_url())

    def test_seed_is_idempotent(self):
        call_command("seed")
        call_command("seed")
        self.assertEqual(Contact.objects.filter(email="ada@example.com").count(), 1)
