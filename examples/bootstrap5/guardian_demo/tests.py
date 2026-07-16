from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from guardian_demo.models import Document


class GuardianTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        from guardian_demo.views import cv_document

        User = get_user_model()
        cls.alice = User.objects.create_user(username="alice-test", password="pw")
        cls.bob = User.objects.create_user(username="bob-test", password="pw")

        cls.alice_doc = Document.objects.create(title="Roadmap 2027", body="Secret plans", owner=cls.alice)
        cls.shared_doc = Document.objects.create(title="Team Handbook", body="For everyone", owner=cls.alice)
        cls.bob_doc = Document.objects.create(title="Bob's Notes", body="", owner=cls.bob)

        for action in ("view", "change", "delete"):
            cv_document.assign_perm(action, cls.alice, cls.alice_doc)
            cv_document.assign_perm(action, cls.alice, cls.shared_doc)
            cv_document.assign_perm(action, cls.bob, cls.bob_doc)
        cv_document.assign_perm("view", cls.bob, cls.shared_doc)  # shared view-only


class DocumentVisibilityTest(GuardianTestCase):
    def test_alice_sees_only_her_documents(self):
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("document-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Roadmap 2027")
        self.assertContains(resp, "Team Handbook")
        self.assertNotContains(resp, "Bob&#x27;s Notes")

    def test_bob_sees_his_and_shared(self):
        self.client.force_login(self.bob)
        resp = self.client.get(reverse("document-list"))
        self.assertContains(resp, "Team Handbook")
        self.assertNotContains(resp, "Roadmap 2027")

    def test_bob_cannot_open_unshared_document(self):
        self.client.force_login(self.bob)
        resp = self.client.get(reverse("document-detail", kwargs={"pk": self.alice_doc.pk}))
        self.assertEqual(resp.status_code, 403)

    def test_bob_cannot_edit_view_only_share(self):
        self.client.force_login(self.bob)
        resp = self.client.get(reverse("document-update", kwargs={"pk": self.shared_doc.pk}))
        self.assertEqual(resp.status_code, 403)


class DocumentCreateTest(GuardianTestCase):
    def test_create_assigns_owner_and_object_perms(self):
        from project.seeding import grant_model_perms

        grant_model_perms(self.alice, Document, actions=("add",))
        self.client.force_login(self.alice)

        resp = self.client.post(reverse("document-create"), {"title": "New Idea", "body": "Draft"})
        self.assertEqual(resp.status_code, 302)

        doc = Document.objects.get(title="New Idea")
        self.assertEqual(doc.owner, self.alice)
        # creator can immediately open and edit it
        self.assertEqual(self.client.get(reverse("document-detail", kwargs={"pk": doc.pk})).status_code, 200)
        self.assertEqual(self.client.get(reverse("document-update", kwargs={"pk": doc.pk})).status_code, 200)


class GuardianSeedTest(TestCase):
    def test_seed_twice_and_shares_one_doc_with_bob(self):
        from django.core.management import call_command

        call_command("seed")
        count = Document.objects.count()
        call_command("seed")
        self.assertEqual(Document.objects.count(), count)

        User = get_user_model()
        bob = User.objects.get(username="bob")
        self.client.force_login(bob)
        resp = self.client.get(reverse("document-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Team Handbook")  # alice's doc, shared view-only
