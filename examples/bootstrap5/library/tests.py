from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from library.models import Author, Book


class LibraryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")
        cls.author = Author.objects.create(first_name="Ursula", last_name="Le Guin")
        cls.book1 = Book.objects.create(title="A Wizard of Earthsea", price=Decimal("7.99"), author=cls.author)
        cls.book2 = Book.objects.create(title="The Dispossessed", price=Decimal("9.99"), author=cls.author)

    def setUp(self):
        self.client.force_login(self.admin)


class AuthorCrudTest(LibraryTestCase):
    def test_list_shows_authors_and_code_snippets(self):
        resp = self.client.get(reverse("author-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Le Guin")
        self.assertContains(resp, "snippet-panels")

    def test_list_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse("author-list"))
        self.assertEqual(resp.status_code, 302)

    def test_filter_narrows_list(self):
        Author.objects.create(first_name="Terry", last_name="Pratchett")
        resp = self.client.get(reverse("author-list"), {"last_name": "guin"})
        self.assertContains(resp, "Le Guin")
        self.assertNotContains(resp, "Pratchett")

    def test_detail(self):
        resp = self.client.get(reverse("author-detail", kwargs={"pk": self.author.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Le Guin")

    def test_create(self):
        data = {"first_name": "Octavia", "last_name": "Butler", "pseudonym": ""}
        resp = self.client.post(reverse("author-create"), data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Author.objects.filter(last_name="Butler").exists())

    def test_update(self):
        data = {"first_name": "Ursula K.", "last_name": "Le Guin", "pseudonym": ""}
        resp = self.client.post(reverse("author-update", kwargs={"pk": self.author.pk}), data)
        self.assertEqual(resp.status_code, 302)
        self.author.refresh_from_db()
        self.assertEqual(self.author.first_name, "Ursula K.")

    def test_delete(self):
        author = Author.objects.create(first_name="To", last_name="Delete")
        # CrispyDeleteForm requires an explicit confirm=True (see tests/test1/test_delete.py)
        resp = self.client.post(reverse("author-delete", kwargs={"pk": author.pk}), {"confirm": True})
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Author.objects.filter(pk=author.pk).exists())


class BookOrderingTest(LibraryTestCase):
    def test_book_list_renders(self):
        resp = self.client.get(reverse("book-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Earthsea")

    def test_move_book_up(self):
        # book2 sits below book1; moving it up swaps the order
        resp = self.client.post(reverse("book-up", kwargs={"pk": self.book2.pk}))
        self.assertEqual(resp.status_code, 302)
        self.book1.refresh_from_db()
        self.book2.refresh_from_db()
        self.assertLess(self.book2.order, self.book1.order)

    def test_move_book_down(self):
        resp = self.client.post(reverse("book-down", kwargs={"pk": self.book1.pk}))
        self.assertEqual(resp.status_code, 302)
        self.book1.refresh_from_db()
        self.book2.refresh_from_db()
        self.assertLess(self.book2.order, self.book1.order)


class LibrarySeedTest(TestCase):
    def test_seed_twice(self):
        from django.core.management import call_command

        call_command("seed")
        authors = Author.objects.count()
        books = Book.objects.count()
        call_command("seed")
        self.assertEqual(Author.objects.count(), authors)
        self.assertEqual(Book.objects.count(), books)
        self.assertGreater(authors, 0)
        self.assertGreater(books, 0)
