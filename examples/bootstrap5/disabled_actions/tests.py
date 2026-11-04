from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from lxml import html as lxml_html
from project.seeding import grant_model_perms

from disabled_actions.models import Ticket


class DisabledActionsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="disabled-actions-test", password="pw")
        grant_model_perms(cls.user, Ticket)
        cls.locked = Ticket.objects.create(title="Frozen ticket", locked=True)
        cls.open = Ticket.objects.create(title="Open ticket", locked=False)

    def setUp(self):
        self.client.force_login(self.user)

    def page(self, url):
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        return lxml_html.fromstring(resp.content)

    def row(self, ticket):
        (row,) = self.page(reverse("lockable_ticket-list")).xpath(f"//tr[td[normalize-space()='{ticket.title}']]")
        (fieldset,) = row.xpath(".//fieldset[@cv-list-container]")
        return fieldset

    def toolbar(self, ticket):
        url = reverse("lockable_ticket-detail", kwargs={"pk": ticket.pk})
        return self.page(url).xpath("//fieldset[@cv-context-container]")[0]

    @staticmethod
    def buttons(container, key):
        return container.xpath(f'.//*[@cv-key="{key}"]')

    def url(self, key, ticket):
        return reverse(f"lockable_ticket-{key}", kwargs={"pk": ticket.pk})


class LockedTicketTest(DisabledActionsTestCase):
    def assert_update_disabled_and_delete_hidden(self, container):
        (update,) = self.buttons(container, "update")
        self.assertIsNotNone(update.get("disabled"))
        self.assertEqual(update.get("data-cv-disabled"), "state")  # not "permission": the user may change
        self.assertIsNone(update.get("href"))
        self.assertEqual(self.buttons(container, "delete"), [])

    def test_list_row_disables_update_and_hides_delete(self):
        self.assert_update_disabled_and_delete_hidden(self.row(self.locked))

    def test_detail_toolbar_disables_update_and_hides_delete(self):
        self.assert_update_disabled_and_delete_hidden(self.toolbar(self.locked))

    def test_lock_toggle_stays_usable(self):
        (lock,) = self.buttons(self.row(self.locked), "lock")
        self.assertIsNone(lock.get("disabled"))

    # action_enabled.md "Enforcement Points": has_permission() returns False -> PermissionDenied (403)
    def test_update_get_and_post_are_refused(self):
        self.assertEqual(self.client.get(self.url("update", self.locked)).status_code, 403)
        resp = self.client.post(self.url("update", self.locked), {"title": "Thawed", "locked": ""})
        self.assertEqual(resp.status_code, 403)
        self.locked.refresh_from_db()
        self.assertEqual(self.locked.title, "Frozen ticket")

    def test_delete_get_and_post_are_refused(self):
        self.assertEqual(self.client.get(self.url("delete", self.locked)).status_code, 403)
        self.assertEqual(self.client.post(self.url("delete", self.locked)).status_code, 403)
        self.assertTrue(Ticket.objects.filter(pk=self.locked.pk).exists())


class OpenTicketTest(DisabledActionsTestCase):
    def assert_update_and_delete_enabled(self, container):
        for key in ("update", "delete"):
            with self.subTest(key=key):
                (button,) = self.buttons(container, key)
                self.assertIsNone(button.get("disabled"))
                self.assertEqual(button.get("href").split("?")[0], self.url(key, self.open))  # + cancel origin query

    def test_list_row_shows_update_and_delete(self):
        self.assert_update_and_delete_enabled(self.row(self.open))

    def test_detail_toolbar_shows_update_and_delete(self):
        self.assert_update_and_delete_enabled(self.toolbar(self.open))

    def test_update_page_renders(self):
        self.assertEqual(self.client.get(self.url("update", self.open)).status_code, 200)


class LockToggleTest(DisabledActionsTestCase):
    def test_lock_toggles_and_flips_the_buttons(self):
        resp = self.client.post(self.url("lock", self.open))
        self.assertEqual(resp.status_code, 302)
        self.open.refresh_from_db()
        self.assertTrue(self.open.locked)
        self.assertEqual(self.client.get(self.url("update", self.open)).status_code, 403)

        self.client.post(self.url("lock", self.open))
        self.open.refresh_from_db()
        self.assertFalse(self.open.locked)
        self.assertEqual(self.client.get(self.url("update", self.open)).status_code, 200)


class SeedTest(TestCase):
    def test_seed_is_idempotent_and_has_both_states(self):
        call_command("seed")
        call_command("seed")
        self.assertTrue(Ticket.objects.filter(locked=True).exists())
        self.assertTrue(Ticket.objects.filter(locked=False).exists())
        self.assertEqual(Ticket.objects.filter(title=Ticket.objects.first().title).count(), 1)
