from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from lxml import html as lxml_html
from project.seeding import grant_model_perms

from action_menus.models import Chore, Step


class ActionMenusTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.alice = User.objects.create_user(username="alice-test", password="pw")
        cls.bob = User.objects.create_user(username="bob-test", password="pw")
        for model in (Chore, Step):
            grant_model_perms(cls.alice, model)
            grant_model_perms(cls.bob, model, actions=("view",))
        cls.chore = Chore.objects.create(title="Take out the trash")

    @staticmethod
    def doc(resp):
        """The page without the code panel, which shows these templates' source (and so their class names)."""
        return lxml_html.fromstring(resp.content.decode().split('id="snippet-panels"')[0])

    def get(self, user, url_name, **kwargs):
        self.client.force_login(user)
        resp = self.client.get(reverse(url_name, kwargs=kwargs or None))
        self.assertEqual(resp.status_code, 200)
        return self.doc(resp)


class ChoreListTest(ActionMenusTestCase):
    def test_row_keeps_inline_buttons_and_menu(self):
        doc = self.get(self.alice, "chore-list")
        fieldset = doc.xpath("//fieldset[@cv-list-container]")[0]
        self.assertEqual([el.get("cv-key") for el in fieldset.xpath("./*[@cv-key]")], ["detail", "up", "down"])
        items = [i.get("cv-key") for i in fieldset.cssselect(".dropdown-item")]
        self.assertEqual(items, ["update", "done", "archive", "list", "delete"])

    def test_table_is_responsive(self):
        doc = self.get(self.alice, "chore-list")
        self.assertTrue(doc.xpath("//div[contains(@class, 'table-responsive')]//td//fieldset[@cv-list-container]"))

    def test_bob_sees_archive_disabled(self):
        doc = self.get(self.bob, "chore-list")
        archive = doc.cssselect('.dropdown-item[cv-key="archive"]')[0]
        self.assertIsNotNone(archive.get("disabled"))
        self.assertEqual(archive.get("data-cv-disabled"), "permission")
        self.assertEqual(doc.cssselect('.dropdown-item[cv-key="update"]'), [])

    def test_german_toggle_label(self):
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("chore-list"), HTTP_ACCEPT_LANGUAGE="de")
        self.assertContains(resp, 'aria-label="Weitere Aktionen"')


class PostActionsTest(ActionMenusTestCase):
    def assert_post_items(self, doc):
        items = doc.cssselect('.dropdown-item[cv-key="done"], .dropdown-item[cv-key="archive"]')
        self.assertTrue(items)
        for item in items:
            self.assertEqual(item.tag, "button")
            self.assertEqual(item.get("data-cv-action"), "submit-form")
            self.assertIsNone(item.get("href"))
            self.assertTrue(doc.xpath(f"//*[@id='{item.get('data-cv-target').lstrip('#')}']"))

    def test_list_post_items_submit_forms(self):
        self.assert_post_items(self.get(self.alice, "chore-list"))

    def test_card_post_items_submit_forms(self):
        self.assert_post_items(self.get(self.alice, "chore-card"))

    def test_toolbar_post_items_submit_forms(self):
        self.assert_post_items(self.get(self.alice, "chore-detail", pk=self.chore.pk))

    def test_toolbar_done_toggles(self):
        doc = self.get(self.alice, "chore-detail", pk=self.chore.pk)
        item = doc.xpath("//fieldset[@cv-context-container]")[0].cssselect('.dropdown-item[cv-key="done"]')[0]
        form = doc.xpath(f"//form[@id='{item.get('data-cv-target')}']")[0]
        self.assertEqual(self.client.post(form.get("action")).status_code, 302)
        self.chore.refresh_from_db()
        self.assertTrue(self.chore.done)


class ChoreDetailTest(ActionMenusTestCase):
    def test_active_detail_in_menu(self):
        doc = self.get(self.alice, "chore-detail", pk=self.chore.pk)
        toolbar = doc.xpath("//fieldset[@cv-context-container]")[0]
        detail = toolbar.cssselect('.dropdown-item[cv-key="detail"]')[0]
        self.assertEqual(detail.get("aria-current"), "page")

    def test_steps_item_uses_button_label(self):
        doc = self.get(self.alice, "chore-detail", pk=self.chore.pk)
        toolbar = doc.xpath("//fieldset[@cv-context-container]")[0]
        steps = toolbar.cssselect('.dropdown-item[cv-key="list"]')
        self.assertIn("Steps", [i.text_content().strip() for i in steps])
        self.assertIn("List", [i.text_content().strip() for i in steps])

    def test_active_update_inline(self):
        doc = self.get(self.alice, "chore-update", pk=self.chore.pk)
        toolbar = doc.xpath("//fieldset[@cv-context-container]")[0]
        self.assertIn("active", toolbar.xpath('./a[@cv-key="update"]')[0].get("class").split())


class ChoreCardTest(ActionMenusTestCase):
    def test_card_menu_has_child_action(self):
        doc = self.get(self.alice, "chore-card")
        card = doc.xpath("//div[contains(@class, 'card') and contains(@class, 'mb-3')]")[0]
        labels = [i.text_content().strip() for i in card.cssselect(".dropdown-item")]
        self.assertIn("Steps", labels)
        self.assertIn("Delete", labels)
