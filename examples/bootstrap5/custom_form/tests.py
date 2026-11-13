from urllib.parse import urlsplit

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from lxml import html as lxml_html
from project.seeding import grant_model_perms

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


class BackLinkTest(CustomFormTestCase):
    def test_detail_and_remind_link_back_to_list(self):
        for url in (reverse("contact-detail", kwargs={"pk": self.contact.pk}), self.remind_url()):
            resp = self.client.get(url)
            self.assertContains(resp, f'href="{reverse("contact-list")}"')


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


class ContactPermissionsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reader = get_user_model().objects.create_user(username="contact-reader")
        grant_model_perms(cls.reader, Contact, actions=("view",))
        cls.contact = Contact.objects.create(name="Reader contact", email="reader@example.com")

    def setUp(self):
        self.client.force_login(self.reader)

    def test_view_only_user_can_read_without_executable_write_links(self):
        remind_url = reverse("contact-remind", kwargs={"pk": self.contact.pk})
        invite_url = reverse("contact-invite")
        for url in (reverse("contact-list"), reverse("contact-detail", kwargs={"pk": self.contact.pk})):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                links = [urlsplit(href).path for href in lxml_html.fromstring(response.content).xpath("//a/@href")]
                self.assertNotIn(remind_url, links)
                self.assertNotIn(invite_url, links)

    def test_view_only_user_cannot_open_or_submit_reminder(self):
        url = reverse("contact-remind", kwargs={"pk": self.contact.pk})
        for method, data in (("get", {}), ("post", {"note": "Do not send"})):
            with self.subTest(method=method):
                response = getattr(self.client, method)(url, data)
                self.assertEqual(response.status_code, 403)
                self.contact.refresh_from_db()
                self.assertIsNone(self.contact.last_reminded_dt)
                self.assertEqual(Contact.objects.count(), 1)
                self.assertEqual(list(get_messages(response.wsgi_request)), [])

    def test_view_only_user_cannot_open_or_submit_invitation(self):
        for method, data in (("get", {}), ("post", {"email": "denied@example.com"})):
            with self.subTest(method=method):
                response = getattr(self.client, method)(reverse("contact-invite"), data)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(Contact.objects.count(), 1)
                self.assertEqual(list(get_messages(response.wsgi_request)), [])


class ContactSeedPermissionsTest(TestCase):
    def test_repeated_seed_preserves_demo_user_permissions_and_actions(self):
        call_command("seed")
        call_command("seed")
        contact = Contact.objects.get(email="ada@example.com")
        for username in ("alice", "bob"):
            with self.subTest(username=username):
                user = get_user_model().objects.get(username=username)
                for action in ("view", "add", "change", "delete"):
                    self.assertTrue(user.has_perm(f"custom_form.{action}_contact"))
                self.client.force_login(user)
                remind_url = reverse("contact-remind", kwargs={"pk": contact.pk})
                self.assertEqual(self.client.get(remind_url).status_code, 200)
                contact.last_reminded_dt = None
                contact.save(update_fields=["last_reminded_dt"])
                response = self.client.post(remind_url, {"note": "Please reply"}, follow=True)
                self.assertEqual(response.status_code, 200)
                contact.refresh_from_db()
                self.assertIsNotNone(contact.last_reminded_dt)
                self.assertEqual([str(m) for m in response.context["messages"]], ["Reminded contact “Ada Lovelace”"])
                invite_url = reverse("contact-invite")
                self.assertEqual(self.client.get(invite_url).status_code, 200)
                email = f"{username}-invited@example.com"
                response = self.client.post(invite_url, {"email": email}, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(Contact.objects.filter(email=email).exists())
                self.assertEqual([m.level for m in response.context["messages"]], [messages.SUCCESS])
