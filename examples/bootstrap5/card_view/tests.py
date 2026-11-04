from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from library.models import Author


class CardViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")
        cls.author = Author.objects.create(first_name="Ursula", last_name="Le Guin")

    def setUp(self):
        self.client.force_login(self.admin)


class AuthorCardTest(CardViewTestCase):
    def test_card_landing_page_renders_with_snippets(self):
        resp = self.client.get(reverse("author_card-card"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Le Guin")
        self.assertContains(resp, "snippet-panels")

    def test_signed_order_single_combo(self):
        resp = self.client.get(reverse("author_card-card"))
        self.assertContains(resp, 'data-cv-action="submit-on-change"')
        self.assertContains(resp, '<option value="-created_dt" selected>Newest first</option>', html=True)
        self.assertNotContains(resp, 'name="dir"')

    def test_signed_order_applies(self):
        Author.objects.create(first_name="Terry", last_name="Pratchett")
        content = self.client.get(reverse("author_card-card"), {"order": "last_name"}).content.decode()
        self.assertLess(content.index("Le Guin"), content.index("Pratchett"))
        content = self.client.get(reverse("author_card-card"), {"order": "-last_name"}).content.decode()
        self.assertLess(content.index("Pratchett"), content.index("Le Guin"))

    def test_paginates_with_seed_data(self):
        call_command("seed")
        resp = self.client.get(reverse("author_card-card"))
        self.assertContains(resp, "page=2")

    def test_detail_renders(self):
        resp = self.client.get(reverse("author_card-detail", kwargs={"pk": self.author.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Le Guin")

    def test_create_update_delete(self):
        resp = self.client.post(reverse("author_card-create"), {"first_name": "Ted", "last_name": "Chiang"})
        self.assertEqual(resp.status_code, 302)
        ted = Author.objects.get(last_name="Chiang")
        resp = self.client.post(
            reverse("author_card-update", kwargs={"pk": ted.pk}), {"first_name": "Theodore", "last_name": "Chiang"}
        )
        self.assertEqual(resp.status_code, 302)
        ted.refresh_from_db()
        self.assertEqual(ted.first_name, "Theodore")
        resp = self.client.post(reverse("author_card-delete", kwargs={"pk": ted.pk}), {"confirm": True})
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Author.objects.filter(pk=ted.pk).exists())

    def test_library_links_unaffected(self):
        resp = self.client.get(reverse("author-detail", kwargs={"pk": self.author.pk}))
        self.assertContains(resp, reverse("author-list"))
        # the navbar links to the Card View feature itself; only the author ViewSet URLs must not leak in
        self.assertNotContains(resp, f"/card-view/author_card/{self.author.pk}/")
        resp = self.client.get(reverse("author_card-detail", kwargs={"pk": self.author.pk}))
        self.assertNotContains(resp, reverse("author-update", kwargs={"pk": self.author.pk}))
