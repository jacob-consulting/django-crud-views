from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from lxml import html as lxml_html
from project.seeding import grant_model_perms

from label_modes.models import Gadget


class LabelModesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="label-modes-test", password="pw")
        grant_model_perms(cls.user, Gadget)
        cls.gadget = Gadget.objects.create(name="Pocket torch")

    def setUp(self):
        self.client.force_login(self.user)

    def page(self, url, **headers):
        resp = self.client.get(url, **headers)
        self.assertEqual(resp.status_code, 200)
        return lxml_html.fromstring(resp.content)

    def row(self, **headers):
        (fieldset,) = self.page(reverse("gadget-list"), **headers).xpath("//td//fieldset[@cv-list-container]")
        return fieldset

    def toolbar(self, **headers):
        url = reverse("gadget-detail", kwargs={"pk": self.gadget.pk})
        return self.page(url, **headers).xpath("//fieldset[@cv-context-container]")[0]

    @staticmethod
    def button(container, key):
        (el,) = container.xpath(f'./*[@cv-key="{key}"]')
        return el

    # the three modes, as PR #305 renders them (tests/test1/test_action_label_mode_render.py)

    def assert_label(self, el, text):
        """Text only: no icon, no tooltip, the visible text is the accessible name."""
        self.assertEqual(el.xpath("./*[@aria-hidden='true']"), [])
        self.assertIsNone(el.get("title"))
        self.assertIsNone(el.get("data-cv-tooltip"))
        self.assertEqual([s.text for s in el.xpath("./span")], [text])
        self.assertIsNone(el.xpath("./span")[0].get("class"))

    def assert_both(self, el, text):
        """Icon and visible text, no tooltip."""
        self.assertEqual(len(el.xpath("./*[@aria-hidden='true']")), 1)
        self.assertIsNone(el.get("title"))
        self.assertIsNone(el.get("data-cv-tooltip"))
        self.assertEqual([s.text for s in el.xpath("./span")], [text])
        self.assertIsNone(el.xpath("./span")[0].get("class"))

    def assert_icon(self, el, location, short, full):
        """Icon only: the full label is visually hidden text (the accessible name), the short label the tooltip."""
        self.assertEqual(len(el.xpath("./*[@aria-hidden='true']")), 1)
        (hidden,) = el.xpath("./span")
        self.assertEqual(hidden.get("class"), "visually-hidden")
        self.assertEqual(hidden.text_content(), full)
        self.assertEqual(el.get("title"), short)
        self.assertEqual(el.get("data-cv-tooltip"), location)


class ListRowTest(LabelModesTestCase):
    def test_detail_is_label_only(self):
        self.assert_label(self.button(self.row(), "detail"), "Detail")

    def test_update_shows_icon_and_label(self):
        self.assert_both(self.button(self.row(), "update"), "Update")

    def test_delete_is_icon_only_with_tooltip_and_hidden_label(self):
        self.assert_icon(self.button(self.row(), "delete"), "list", "Delete", "Delete Gadget “Pocket torch”")


class DetailToolbarTest(LabelModesTestCase):
    def test_list_is_label_only(self):
        self.assert_label(self.button(self.toolbar(), "list"), "List")

    def test_update_shows_icon_and_label(self):
        self.assert_both(self.button(self.toolbar(), "update"), "Update")

    def test_delete_is_icon_only_with_tooltip_and_hidden_label(self):
        self.assert_icon(self.button(self.toolbar(), "delete"), "context", "Delete", "Delete Gadget “Pocket torch”")

    def test_german_tooltip_and_hidden_label(self):
        delete = self.button(self.toolbar(HTTP_ACCEPT_LANGUAGE="de"), "delete")
        self.assertEqual(delete.get("title"), "Löschen")
        self.assertIn("Pocket torch", delete.xpath("./span")[0].text_content())


class SeedTest(TestCase):
    def test_seed_is_idempotent(self):
        call_command("seed")
        call_command("seed")
        self.assertEqual(Gadget.objects.filter(name="Pocket torch").count(), 1)
