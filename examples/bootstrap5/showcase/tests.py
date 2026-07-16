from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from showcase.models import Recipe


class ShowcaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")
        cls.recipe = Recipe.objects.create(
            title="Shakshuka", description="Eggs poached in tomato sauce.", difficulty="easy", servings=2
        )

    def setUp(self):
        self.client.force_login(self.admin)


class RecipeCardTest(ShowcaseTestCase):
    def test_card_landing_page_renders_with_snippets(self):
        resp = self.client.get(reverse("recipe-card"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Shakshuka")
        self.assertContains(resp, "snippet-panels")

    def test_detail_shows_fieldset_groups(self):
        resp = self.client.get(reverse("recipe-detail", kwargs={"pk": self.recipe.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Basics")
        self.assertContains(resp, "Details")

    def test_create_with_fieldset_form(self):
        data = {"title": "Ratatouille", "description": "Vegetable stew.", "difficulty": "medium", "servings": 4}
        resp = self.client.post(reverse("recipe-create"), data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Recipe.objects.filter(title="Ratatouille").exists())

    def test_favorite_action_toggles(self):
        self.assertFalse(self.recipe.favorite)
        resp = self.client.post(reverse("recipe-favorite", kwargs={"pk": self.recipe.pk}))
        self.assertEqual(resp.status_code, 302)
        self.recipe.refresh_from_db()
        self.assertTrue(self.recipe.favorite)


class ShowcaseSeedTest(TestCase):
    def test_seed_twice(self):
        from django.core.management import call_command

        call_command("seed")
        count = Recipe.objects.count()
        call_command("seed")
        self.assertEqual(Recipe.objects.count(), count)
        self.assertGreater(count, 0)
