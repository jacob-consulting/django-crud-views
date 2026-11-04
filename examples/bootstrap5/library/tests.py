from decimal import Decimal
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.core import signing
from django.test import TestCase
from django.urls import reverse
from lxml import html

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

    def test_update_cancel_returns_to_detail_origin(self):
        self.assert_cancel_round_trip("detail")

    def test_update_cancel_returns_to_list_origin(self):
        self.assert_cancel_round_trip("list")

    def assert_cancel_round_trip(self, origin):
        origin_url = reverse(f"author-{origin}", kwargs={"pk": self.author.pk} if origin == "detail" else {})
        update_url = reverse("author-update", kwargs={"pk": self.author.pk})
        query = "last_name=guin&x=&x=%3Ctag%3E%26%22"
        resp = self.client.get(origin_url + "?" + query)
        links = html.fromstring(resp.content).xpath("//a/@href")
        link = next(value for value in links if urlsplit(value).path == update_url)
        params = parse_qs(urlsplit(link).query)
        self.assertEqual(params["cv_from"], [origin])
        self.assertEqual(len(params["cv_from_cancel"]), 1)
        capture = signing.Signer(salt="crud_views.cancel.v1").unsign_object(params["cv_from_cancel"][0])
        self.assertEqual(capture, {"v": 1, "origin": origin, "query": query, "viewset": ["", "author"], "parents": {}})
        form = self.client.get(link)
        (cancel,) = html.fromstring(form.content).xpath("//form//*[@data-cv-cancel-url]/@data-cv-cancel-url")
        self.assertEqual(urlsplit(cancel).path, origin_url)
        restored = parse_qs(urlsplit(cancel).query, keep_blank_values=True)
        expected = parse_qs(query, keep_blank_values=True)
        if origin == "list":
            expected["cv_from_restore"] = ["1"]
        self.assertEqual(restored, expected)
        returned = self.client.get(cancel)
        self.assertEqual(returned.status_code, 200)
        self.assertEqual(returned.wsgi_request.GET.getlist("x"), ["", '<tag>&"'])
        self.assertEqual(Author.objects.get(pk=self.author.pk).first_name, "Ursula")

    def test_legacy_key_only_cancel_stays_uncaptured(self):
        update_url = reverse("author-update", kwargs={"pk": self.author.pk})
        for origin in ("detail", "list"):
            with self.subTest(origin=origin):
                expected = reverse(f"author-{origin}", kwargs={"pk": self.author.pk} if origin == "detail" else {})
                response = self.client.get(update_url, {"cv_from": origin})
                self.assertContains(response, f'data-cv-cancel-url="{expected}"')

    def test_update_success_returns_to_detail_origin(self):
        detail_url = reverse("author-detail", kwargs={"pk": self.author.pk})
        update_url = reverse("author-update", kwargs={"pk": self.author.pk})
        data = {"first_name": "Ursula K.", "last_name": "Le Guin", "pseudonym": ""}
        resp = self.client.post(f"{update_url}?cv_from=detail", data)
        self.assertRedirects(resp, detail_url, fetch_redirect_response=False)

    def test_update_success_returns_to_list_origin(self):
        update_url = reverse("author-update", kwargs={"pk": self.author.pk})
        data = {"first_name": "Ursula K.", "last_name": "Le Guin", "pseudonym": ""}
        resp = self.client.post(f"{update_url}?cv_from=list", data)
        self.assertRedirects(resp, reverse("author-list"), fetch_redirect_response=False)


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


class ProtectedDeletePreviewTest(LibraryTestCase):
    def make_contract(self):
        from library import models

        self.assertTrue(hasattr(models, "Contract"), "Library must provide a protected publishing Contract")
        self.contract = models.Contract.objects.create(title="Earthsea publishing contract", author=self.author)
        self.delete_url = reverse("author-delete", kwargs={"pk": self.author.pk})
        self.detail_url = reverse("contract-detail", kwargs={"pk": self.contract.pk})

    def assert_rows_preserved(self):
        self.assertTrue(Author.objects.filter(pk=self.author.pk).exists())
        self.assertTrue(type(self.contract).objects.filter(pk=self.contract.pk).exists())
        self.assertEqual(
            set(Book.objects.filter(author=self.author).values_list("pk", flat=True)), {self.book1.pk, self.book2.pk}
        )

    def assert_blocked(self, response, status=200, url=None):
        self.assertEqual(response.status_code, status)
        self.assertTrue(response.context["has_protected_objects"])
        self.assertEqual(response.context["protected_objects"], [{"obj": self.contract, "url": url}])
        document = html.fromstring(response.content)
        self.assertFalse(document.xpath('//form[.//*[@name="confirm"]]'))
        self.assert_rows_preserved()
        return document

    def test_protected_page_and_modal_link_to_full_detail(self):
        self.make_contract()
        for modal in (False, True):
            with self.subTest(modal=modal):
                response = self.client.get(self.delete_url, HTTP_X_CV_MODAL="true" if modal else "false")
                document = self.assert_blocked(response, url=self.detail_url)
                (link,) = document.xpath("//a[@href=$url]", url=self.detail_url)
                self.assertEqual(link.text_content(), self.contract.title)
                self.assertFalse(any(key.startswith("data-cv-modal") for key in link.attrib))
                self.assertEqual(bool(document.xpath('//div[@class="modal-body"]')), modal)
                detail = self.client.get(link.get("href"))
                self.assertContains(detail, self.contract.title)
                self.assertContains(detail, str(self.author))
                self.assertContains(detail, "<!DOCTYPE html>", html=False)

    def test_confirmed_page_and_modal_posts_preserve_rows(self):
        self.make_contract()
        for modal in (False, True):
            with self.subTest(modal=modal):
                response = self.client.post(
                    self.delete_url, {"confirm": True}, HTTP_X_CV_MODAL="true" if modal else "false"
                )
                self.assert_blocked(response, status=422 if modal else 200, url=self.detail_url)

    def test_visible_blocker_falls_back_to_text(self):
        self.make_contract()
        from library.views import AuthorDeleteView, ContractDetailView, cv_contract

        for label, override in (
            ("disabled", patch.object(AuthorDeleteView, "cv_link_related_objects", False)),
            ("missing", patch.dict(cv_contract._views, {}, clear=True)),
            (
                "inaccessible",
                patch.object(ContractDetailView, "get_queryset", lambda view: type(self.contract).objects.none()),
            ),
        ):
            with self.subTest(fallback=label), override:
                for modal in (False, True):
                    response = self.client.post(
                        self.delete_url, {"confirm": True}, HTTP_X_CV_MODAL="true" if modal else "false"
                    )
                    document = self.assert_blocked(response, status=422 if modal else 200)
                    self.assertIn(self.contract.title, document.text_content())
                    self.assertFalse(document.xpath("//a[@href=$url]", url=self.detail_url))

    def test_unprotected_author_previews_book_links_and_cascades(self):
        url = reverse("author-delete", kwargs={"pk": self.author.pk})
        response = self.client.get(url)
        self.assertFalse(response.context["has_protected_objects"])
        document = html.fromstring(response.content)
        for book in (self.book1, self.book2):
            self.assertTrue(document.xpath("//a[@href=$url]", url=reverse("book-detail", kwargs={"pk": book.pk})))
        self.assertEqual(self.client.post(url, {"confirm": True}).status_code, 302)
        self.assertFalse(Author.objects.filter(pk=self.author.pk).exists())
        self.assertFalse(Book.objects.filter(pk__in=[self.book1.pk, self.book2.pk]).exists())


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

    def test_protected_seed_is_idempotent_and_permissions_are_distinct(self):
        from django.core.management import call_command

        from library.models import Contract
        from library.seed import AUTHORS

        call_command("seed")
        self.assertEqual(Contract.objects.count(), 1)
        contract = Contract.objects.get(title="Earthsea publishing contract")
        self.assertEqual(str(contract.author), "Ursula Le Guin")
        call_command("seed")
        self.assertEqual(list(Contract.objects.values_list("pk", flat=True)), [contract.pk])
        self.assertEqual(Author.objects.count(), len(AUTHORS))
        self.assertEqual(Book.objects.count(), sum(len(books) for _, _, _, books in AUTHORS))
        delete_url = reverse("author-delete", kwargs={"pk": contract.author_id})
        detail_url = reverse("contract-detail", kwargs={"pk": contract.pk})
        for username in ("alice", "bob"):
            user = get_user_model().objects.get(username=username)
            self.assertEqual(user.has_perm("library.view_contract"), username == "alice")
            for model in ("author", "book"):
                for action in ("view", "add", "change", "delete"):
                    self.assertTrue(user.has_perm(f"library.{action}_{model}"))
            for action in ("add", "change", "delete"):
                self.assertFalse(user.has_perm(f"library.{action}_contract"))
            self.client.force_login(user)
            for modal in (False, True):
                response = self.client.get(delete_url, HTTP_X_CV_MODAL="true" if modal else "false")
                self.assertTrue(response.context["has_protected_objects"])
                if username == "alice":
                    self.assertEqual(response.context["protected_objects"], [{"obj": contract, "url": detail_url}])
                    self.assertContains(response, f'href="{detail_url}"')
                else:
                    self.assertEqual(response.context["protected_objects"], [])
                    self.assertNotContains(response, contract.title)
                    self.assertNotContains(response, detail_url)
                    self.assertContains(response, "Other objects still reference this one")
                    blocked = self.client.post(
                        delete_url, {"confirm": True}, HTTP_X_CV_MODAL="true" if modal else "false"
                    )
                    self.assertEqual(blocked.status_code, 422 if modal else 200)
                    self.assertTrue(blocked.context["has_protected_objects"])
                    self.assertEqual(blocked.context["protected_objects"], [])
                    self.assertNotContains(blocked, contract.title, status_code=blocked.status_code)
                    self.assertNotContains(blocked, detail_url, status_code=blocked.status_code)
            self.assertEqual(self.client.get(detail_url).status_code, 200 if username == "alice" else 403)
            other = Author.objects.get(last_name="Pratchett")
            preview = self.client.get(reverse("author-delete", kwargs={"pk": other.pk}))
            self.assertFalse(preview.context["has_protected_objects"])
        self.assertTrue(Author.objects.filter(pk=contract.author_id).exists())
        self.assertTrue(Contract.objects.filter(pk=contract.pk).exists())
        self.assertEqual(Book.objects.filter(author_id=contract.author_id).count(), 2)

    def test_library_teaches_protected_delete_exercise(self):
        from django.core.management import call_command

        call_command("seed")
        self.client.force_login(get_user_model().objects.get(username="alice"))
        response = self.client.get(reverse("author-list"))
        for instruction in ("Alice", "Bob", "Ursula", "Guin", "full page", "Contract.author"):
            self.assertContains(response, instruction)
