from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from lxml import html
from project.seeding import grant_model_perms


class BulkSelectionLandingTest(TestCase):
    def test_table_landing_offers_three_bulk_actions(self):
        user = get_user_model().objects.create_superuser(username="admin", password="pw")
        self.client.force_login(user)
        response = self.client.get("/bulk-selection/document/")
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        self.assertEqual(
            tree.xpath("//*[@data-cv-bulk-action]/@data-cv-bulk-action"),
            ["bulk_delete", "archive", "assign_owner"],
        )


class BulkSelectionTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        from bulk_selection.models import Document

        cls.Document = Document
        cls.user = get_user_model().objects.create_user(username="alice", password="pw")
        cls.owner = get_user_model().objects.create_user(username="bob", password="pw")
        grant_model_perms(cls.user, Document, actions=("view", "add", "change", "delete"))
        cls.first = Document.objects.create(title="First draft")
        cls.second = Document.objects.create(title="Second draft")
        cls.locked = Document.objects.create(title="Locked draft", is_locked=True)
        cls.published = Document.objects.create(title="Published", status="published")

    def setUp(self):
        self.client.force_login(self.user)

    def source(self, key="list"):
        response = self.client.get(reverse(f"bulk_document-{key}"))
        self.assertEqual(response.status_code, 200)
        return response

    def destination(self, key, source="list"):
        tree = html.fromstring(self.source(source).content)
        return tree.xpath(f'//*[@data-cv-bulk-action="{key}"]/@formaction')[0]

    def review(self, destination, objects):
        return self.client.post(destination, {"cv_bulk_stage": "review", "cv_bulk_ids": [o.pk for o in objects]})

    def confirm(self, destination, review, **fields):
        self.assertEqual(review.status_code, 200)
        tree = html.fromstring(review.content)
        data = {
            name: tree.xpath(f'//form//input[@name="{name}"]/@value')
            for name in ("cv_bulk_stage", "cv_bulk_ids", "cv_bulk_blocked_ids")
        }
        return self.client.post(destination, {**data, **fields}, follow=True)

    def assert_unchanged(self):
        self.assertEqual(self.Document.objects.filter(status="draft").count(), 3)
        self.assertEqual(self.Document.objects.filter(owner__isnull=False).count(), 0)
        self.assertEqual(self.Document.objects.count(), 4)


class SourceTest(BulkSelectionTestCase):
    def test_table_has_selection_and_delete_first(self):
        tree = html.fromstring(self.source().content)
        self.assertEqual(len(tree.xpath('//input[@name="cv_bulk_ids"]')), 4)
        self.assertEqual(
            tree.xpath("//*[@data-cv-bulk-action]/@data-cv-bulk-action"),
            ["bulk_delete", "archive", "assign_owner"],
        )
        self.assertEqual(len(tree.xpath(f'//a[@href="{reverse("bulk_document-card")}"]')), 1)

    def test_cards_offer_ordering_archive_and_assignment(self):
        tree = html.fromstring(self.source("card").content)
        self.assertEqual(len(tree.xpath('//input[@name="cv_bulk_ids"]')), 4)
        self.assertEqual(tree.xpath("//*[@data-cv-bulk-action]/@data-cv-bulk-action"), ["archive", "assign_owner"])
        self.assertEqual(len(tree.xpath('//form[@id="cv-card-order-form"]')), 1)
        self.assertEqual(
            tree.xpath('//form[@id="cv-card-order-form"]//select[@name="order"]/option/@value'),
            ["title", "status"],
        )

    def test_view_only_user_has_no_bulk_controls_and_cannot_enter_actions(self):
        reader = get_user_model().objects.create_user(username="reader", password="pw")
        grant_model_perms(reader, self.Document, actions=("view",))
        self.client.force_login(reader)
        before = list(self.Document.objects.values())
        for source in ("list", "card"):
            tree = html.fromstring(self.source(source).content)
            self.assertFalse(tree.xpath('//*[@data-cv-bulk or @data-cv-bulk-action] | //input[@name="cv_bulk_ids"]'))
        for action in ("bulk_delete", "archive", "assign_owner"):
            for stage in ("review", "execute"):
                with self.subTest(action=action, stage=stage):
                    response = self.client.post(
                        reverse(f"bulk_document-{action}"),
                        {"cv_bulk_stage": stage, "cv_bulk_ids": [self.first.pk]},
                    )
                    self.assertEqual(response.status_code, 403)
        self.assertEqual(list(self.Document.objects.values()), before)
        self.assert_unchanged()


class DeleteTest(BulkSelectionTestCase):
    def test_mixed_delete_reviews_then_deletes_only_eligible_documents(self):
        destination = self.destination("bulk_delete")
        review = self.review(destination, [self.first, self.second, self.locked])
        self.assertContains(review, "Locked documents cannot be deleted.")
        self.assertContains(review, "Locked draft")
        self.assert_unchanged()
        response = self.confirm(destination, review)
        self.assertEqual([str(m) for m in response.context["messages"]], ["2 documents deleted."])
        self.assertQuerySetEqual(self.Document.objects.values_list("title", flat=True), ["Locked draft", "Published"])

    def test_single_delete_uses_the_same_locked_rule(self):
        url = reverse("bulk_document-delete", kwargs={"pk": self.locked.pk})
        self.assertContains(self.client.get(url), "Locked documents cannot be deleted.")
        self.assertContains(self.client.post(url), "Locked documents cannot be deleted.")
        self.assertTrue(self.Document.objects.filter(pk=self.locked.pk).exists())


class ArchiveTest(BulkSelectionTestCase):
    def test_all_eligible_selection_archives_immediately_and_returns_to_source(self):
        for source in ("list", "card"):
            with self.subTest(source=source):
                self.Document.objects.filter(pk__in=[self.first.pk, self.second.pk]).update(status="draft")
                response = self.review(self.destination("archive", source), [self.first, self.second])
                self.assertRedirects(response, reverse(f"bulk_document-{source}"), fetch_redirect_response=False)
                page = self.client.get(response.url)
                self.assertEqual([str(m) for m in page.context["messages"]], ["2 documents archived."])
                self.assertEqual(self.Document.objects.filter(status="archived").count(), 2)

    def test_mixed_selection_writes_only_after_confirmation(self):
        destination = self.destination("archive")
        review = self.review(destination, [self.first, self.second, self.locked, self.published])
        self.assertContains(review, "Locked documents cannot be archived.")
        self.assertContains(review, "Only drafts can be archived.")
        self.assert_unchanged()
        response = self.confirm(destination, review)
        self.assertEqual([str(m) for m in response.context["messages"]], ["2 documents archived."])
        self.assertEqual(self.Document.objects.filter(status="archived").count(), 2)
        self.locked.refresh_from_db()
        self.published.refresh_from_db()
        self.assertEqual(self.locked.status, "draft")
        self.assertEqual(self.published.status, "published")


class AssignOwnerTest(BulkSelectionTestCase):
    def test_one_form_confirms_eligible_documents_and_assigns_owner(self):
        destination = self.destination("assign_owner", "card")
        review = self.review(destination, [self.first, self.second, self.locked])
        self.assertContains(review, "First draft")
        self.assertContains(review, "Second draft")
        self.assertContains(review, 'name="owner"')
        self.assertContains(review, "Locked documents cannot be reassigned.")
        self.assertFalse(review.context["form"].is_bound)
        self.assert_unchanged()
        response = self.confirm(destination, review, owner=self.owner.pk)
        self.assertEqual(response.redirect_chain[-1][0], reverse("bulk_document-card"))
        self.assertEqual([str(m) for m in response.context["messages"]], ["Owner assigned to 2 documents."])
        self.assertEqual(self.Document.objects.filter(owner=self.owner).count(), 2)
        self.locked.refresh_from_db()
        self.assertIsNone(self.locked.owner)

    def test_missing_owner_is_invalid_and_writes_nothing(self):
        destination = self.destination("assign_owner")
        response = self.confirm(destination, self.review(destination, [self.first]), owner="")
        self.assertTrue(response.context["form"].errors["owner"])
        self.assert_unchanged()

    def test_owner_choices_reject_inactive_users_and_superusers(self):
        users = get_user_model()
        outsiders = [
            users.objects.create_user(username="inactive", is_active=False),
            users.objects.create_superuser(username="admin", password="pw"),
        ]
        destination = self.destination("assign_owner")
        for outsider in outsiders:
            with self.subTest(owner=outsider.username):
                review = self.review(destination, [self.first])
                self.assertEqual(list(review.context["form"].fields["owner"].queryset), [self.user, self.owner])
                response = self.confirm(destination, review, owner=outsider.pk)
                self.assertTrue(response.context["form"].errors["owner"])
                self.assert_unchanged()


class NativeCancelTest(BulkSelectionTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.Document.objects.bulk_create([cls.Document(title=f"Extra {i:02}") for i in range(20)])

    def test_cancel_links_preserve_source_state_without_mutations(self):
        before = list(self.Document.objects.order_by("pk").values())
        for source, query in (
            ("list", {"page": "2", "sort": "title"}),
            ("card", {"page": "2", "order": "title", "dir": "asc"}),
        ):
            cases = [
                ("archive", [self.first, self.locked], False),
                ("archive", [self.locked, self.published], False),
                ("assign_owner", [self.first], False),
                ("assign_owner", [self.first], True),
            ]
            if source == "list":
                cases.append(("bulk_delete", [self.first], False))
            for action, objects, invalid in cases:
                with self.subTest(source=source, action=action, invalid=invalid, ids=[o.pk for o in objects]):
                    page = self.client.get(reverse(f"bulk_document-{source}"), query)
                    self.assertEqual(page.status_code, 200)
                    tree = html.fromstring(page.content)
                    destination = tree.xpath(f'//*[@data-cv-bulk-action="{action}"]/@formaction')[0]
                    review = self.review(destination, objects)
                    if invalid:
                        review = self.confirm(destination, review, owner="")
                        self.assertTrue(review.context["form"].errors["owner"])
                    self.assertEqual(review.status_code, 200)
                    tree = html.fromstring(review.content)
                    links = tree.xpath('//a[normalize-space(.)="Cancel"]')
                    self.assertEqual(len(links), 1)
                    href = links[0].get("href")
                    self.assertTrue(href)
                    self.assertEqual(urlsplit(href).path, reverse(f"bulk_document-{source}"))
                    self.assertEqual(
                        parse_qs(urlsplit(href).query),
                        {**{key: [value] for key, value in query.items()}, "cv_from_restore": ["1"]},
                    )
                    # Follow the actual anchor as a native GET, without submitting the owner form.
                    returned = self.client.get(href)
                    self.assertEqual(returned.status_code, 200)
                    if source == "list":
                        self.assertEqual(returned.context["table"].page.number, 2)
                        self.assertEqual(str(returned.context["table"].order_by), "title")
                    else:
                        self.assertEqual(returned.context["page_obj"].number, 2)
                        self.assertEqual(returned.wsgi_request.GET["order"], "title")
                        self.assertEqual(returned.wsgi_request.GET["dir"], "asc")
                    self.assertEqual(list(self.Document.objects.order_by("pk").values()), before)


class SeedTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = get_user_model().objects.create_user(username="alice", password="pw")
        cls.bob = get_user_model().objects.create_user(username="bob", password="pw")

    def test_seed_dataset_permissions_and_page_counts(self):
        from bulk_selection.models import Document
        from bulk_selection.seed import seed

        seed()
        self.assertEqual(
            list(Document.objects.values_list("title", flat=True)), [f"Document {i:02}" for i in range(1, 25)]
        )
        self.assertEqual(Document.objects.filter(status="draft", is_locked=False).count(), 20)
        self.assertEqual(
            list(Document.objects.filter(is_locked=True).values_list("title", flat=True)),
            ["Document 03", "Document 09"],
        )
        self.assertEqual(
            list(Document.objects.filter(status="published").values_list("title", flat=True)),
            ["Document 05", "Document 17"],
        )
        self.assertFalse(Document.objects.filter(owner__isnull=False).exists())
        for user in (self.alice, self.bob):
            for action in ("view", "add", "change", "delete"):
                self.assertTrue(user.has_perm(f"bulk_selection.{action}_document"))
        self.client.force_login(self.alice)
        table = self.client.get(reverse("bulk_document-list"))
        cards = self.client.get(reverse("bulk_document-card"))
        self.assertEqual(table.context["table"].paginator.num_pages, 3)
        self.assertEqual(cards.context["paginator"].num_pages, 4)
        self.assertEqual(len(table.context["table"].page.object_list), 10)
        self.assertEqual(len(cards.context["page_obj"]), 6)
        before = list(Document.objects.values())
        seed()
        self.assertEqual(list(Document.objects.values()), before)
        Document.objects.filter(title__in=["Document 01", "Document 02"]).delete()
        table = self.client.get(reverse("bulk_document-list"), {"page": 2})
        cards = self.client.get(reverse("bulk_document-card"), {"page": 2, "order": "title"})
        self.assertEqual(table.status_code, 200)
        self.assertEqual(table.context["table"].page.number, 2)
        self.assertEqual(
            [document.title for document in cards.context["page_obj"]],
            ["Document 09", "Document 10", "Document 11", "Document 12", "Document 13", "Document 14"],
        )

    def test_seed_keeps_edits_and_recreates_missing_documents(self):
        from bulk_selection.models import Document
        from bulk_selection.seed import seed

        seed()
        Document.objects.filter(title="Document 01").update(status="archived", is_locked=True, owner=self.alice)
        Document.objects.filter(title="Document 02").delete()
        seed()
        changed = Document.objects.get(title="Document 01")
        self.assertEqual((changed.status, changed.is_locked, changed.owner), ("archived", True, self.alice))
        restored = Document.objects.get(title="Document 02")
        self.assertEqual((restored.status, restored.is_locked, restored.owner), ("draft", False, None))
        self.assertEqual(Document.objects.count(), 24)

    def test_migration_matches_model(self):
        call_command("makemigrations", "bulk_selection", check=True, dry_run=True, verbosity=0)
