from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse

from crud_views.lib.settings import crud_views_settings
from guardian_demo.models import Document, Note


@override_settings(DEBUG=False)
class DeveloperGuardianTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        from io import StringIO

        from django.core.management import call_command

        call_command("seed", stdout=StringIO())

    def setUp(self):
        self.developer = get_user_model().objects.get(username="developer")
        self.client.force_login(self.developer)

    def test_seeded_documents_and_notes_have_object_reads(self):
        from guardian.shortcuts import get_perms

        self.assertTrue(self.developer.has_perm("guardian_demo.view_document", Document.objects.first()))
        for model in (Document, Note):
            for obj in model.objects.all():
                with self.subTest(model=model.__name__, pk=obj.pk):
                    self.assertEqual(set(get_perms(self.developer, obj)), {f"view_{model._meta.model_name}"})
        self.assertEqual(self.client.get(reverse("document-manage")).status_code, 200)
        listing = self.client.get(reverse("document-list"))
        for doc in Document.objects.all():
            self.assertContains(listing, doc.title)
            self.assertEqual(self.client.get(reverse("document-detail", kwargs={"pk": doc.pk})).status_code, 200)
            for key in ("list", "manage"):
                self.assertEqual(
                    self.client.get(reverse(f"note-{key}", kwargs={"document_pk": doc.pk})).status_code, 200
                )
            for note in doc.notes.all():
                kwargs = {"document_pk": doc.pk, "pk": note.pk}
                self.assertEqual(self.client.get(reverse("note-detail", kwargs=kwargs)).status_code, 200)

    def test_parent_revocation_denies_nested_reads_and_diagnostics(self):
        from guardian.shortcuts import remove_perm

        note = Note.objects.first()
        remove_perm("guardian_demo.view_document", self.developer, note.document)
        actor = get_user_model().objects.get(pk=self.developer.pk)
        self.assertTrue(actor.has_perm("guardian_demo.view_document"))
        self.assertTrue(actor.groups.filter(name=crud_views_settings.manage_group).exists())
        self.assertTrue(actor.has_perm("guardian_demo.view_note", note))
        self.client.force_login(actor)
        for key in ("list", "manage", "detail"):
            kwargs = {"document_pk": note.document_id}
            if key == "detail":
                kwargs["pk"] = note.pk
            self.assertEqual(self.client.get(reverse(f"note-{key}", kwargs=kwargs)).status_code, 403)

    def test_repeated_seed_preserves_grants_owners_and_shares_and_excludes_unseeded_objects(self):
        from guardian.models import UserObjectPermission
        from guardian.shortcuts import get_perms

        from guardian_demo.seed import seed

        outsider = Document.objects.create(title="Unseeded", body="Private", owner=Document.objects.first().owner)
        note = Note.objects.create(document=outsider, author=outsider.owner, text="Unseeded note")
        models = (Document, Note, UserObjectPermission)
        before = {model: list(model.objects.order_by("pk").values()) for model in models}
        seed()
        self.assertEqual({model: list(model.objects.order_by("pk").values()) for model in models}, before)
        actor = get_user_model().objects.get(pk=self.developer.pk)
        self.assertEqual(get_perms(actor, outsider), [])
        self.assertEqual(get_perms(actor, note), [])
        self.assertEqual(self.client.get(reverse("document-detail", kwargs={"pk": outsider.pk})).status_code, 403)
        self.assertEqual(self.client.get(reverse("note-manage", kwargs={"document_pk": outsider.pk})).status_code, 403)

    def test_document_and_note_mutations_have_no_effect(self):
        before = {model: list(model.objects.order_by("pk").values()) for model in (Document, Note)}
        doc = Document.objects.first()
        note = Note.objects.first()
        for key in ("create", "update", "delete"):
            cases = (
                ("document", {} if key == "create" else {"pk": doc.pk}, {"title": "Forbidden", "body": "No"}),
                (
                    "note",
                    {"document_pk": note.document_id, **({} if key == "create" else {"pk": note.pk})},
                    {"text": "Forbidden"},
                ),
            )
            for name, kwargs, data in cases:
                with self.subTest(name=name, key=key):
                    self.assertEqual(self.client.post(reverse(f"{name}-{key}", kwargs=kwargs), data).status_code, 403)
        self.assertEqual({model: list(model.objects.order_by("pk").values()) for model in (Document, Note)}, before)

    def test_conflicting_user_and_group_object_grants_are_named_and_preserved(self):
        from django.core.management import CommandError
        from guardian.shortcuts import assign_perm, get_perms, remove_perm

        from guardian_demo.seed import seed

        group = self.developer.groups.get()
        for obj in (Document.objects.first(), Note.objects.first()):
            perm = f"change_{obj._meta.model_name}"
            for recipient in (self.developer, group):
                with self.subTest(model=obj._meta.label, recipient=str(recipient)):
                    assign_perm(perm, recipient, obj)
                    with self.assertRaisesRegex(CommandError, f"{obj._meta.label}.*{obj.pk}.*{perm}"):
                        seed()
                    self.assertIn(perm, get_perms(recipient, obj))
                    remove_perm(perm, recipient, obj)


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
        # the document list links to each document's notes
        resp = self.client.get(reverse("document-list"))
        self.assertContains(resp, reverse("note-list", kwargs={"document_pk": self.alice_doc.pk}))


class NoteAncestorTest(GuardianTestCase):
    """Notes nest under a document: Read needs view on the Document, Write needs change on it."""

    @classmethod
    def setUpTestData(cls):
        from guardian_demo.views import cv_document, cv_note

        super().setUpTestData()
        cls.handbook_note = Note.objects.create(
            document=cls.shared_doc, author=cls.alice, text="Onboarding checklist added"
        )
        for action in ("view", "change", "delete"):
            cv_note.assign_perm(action, cls.alice, cls.handbook_note)
        cv_note.assign_perm("view", cls.bob, cls.handbook_note)
        for action in ("view", "change"):
            cv_document.assign_perm(action, cls.alice, cls.bob_doc)

    def test_bob_reads_notes_of_shared_document_but_cannot_add(self):
        self.client.force_login(self.bob)
        kwargs = {"document_pk": self.shared_doc.pk}
        resp = self.client.get(reverse("note-list", kwargs=kwargs))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Onboarding checklist added")
        # Write gate: change on the Document; bob holds view only
        self.assertEqual(self.client.get(reverse("note-create", kwargs=kwargs)).status_code, 403)
        count = Note.objects.count()
        self.assertEqual(self.client.post(reverse("note-create", kwargs=kwargs), {"text": "x"}).status_code, 403)
        self.assertEqual(Note.objects.count(), count)

    def test_bob_cannot_list_notes_of_unshared_document(self):
        self.client.force_login(self.bob)
        resp = self.client.get(reverse("note-list", kwargs={"document_pk": self.alice_doc.pk}))
        self.assertEqual(resp.status_code, 403)

    def test_alice_adds_note_to_bobs_document_and_owner_may_edit_it(self):
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("note-create", kwargs={"document_pk": self.bob_doc.pk}), {"text": "Changelog reviewed"}
        )
        self.assertEqual(resp.status_code, 302)
        note = Note.objects.get(text="Changelog reviewed")
        self.assertEqual(note.author, self.alice)
        self.assertEqual(note.document, self.bob_doc)
        kwargs = {"document_pk": self.bob_doc.pk, "pk": note.pk}
        self.assertEqual(self.client.get(reverse("note-update", kwargs=kwargs)).status_code, 200)
        # the document owner gets the note grants from NoteCreateView.cv_form_valid
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(reverse("note-detail", kwargs=kwargs)).status_code, 200)
        self.assertEqual(self.client.get(reverse("note-update", kwargs=kwargs)).status_code, 200)

    @override_settings(DEBUG=False)
    def test_manage_pages_report_ancestor_policy(self):
        from guardian_demo.views import cv_document

        manager = get_user_model().objects.create_user(username="manager-test", password="pw")
        manager.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
        cv_document.assign_perm("view", manager, self.shared_doc)
        self.client.force_login(manager)

        resp = self.client.get(reverse("document-manage"))
        self.assertEqual(resp.status_code, 200)
        policy = resp.context["ancestor_policy"]
        self.assertEqual(
            policy["as_ancestor"],
            {"provider": "guardian", "effective_provider": "guardian", "accept_global_perms": False},
        )
        self.assertIsNone(policy["requests"])

        resp = self.client.get(reverse("note-manage", kwargs={"document_pk": self.shared_doc.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["guardian_config"]["parent_viewset"], "document (ancestor provider: guardian)")
        requests = resp.context["ancestor_policy"]["requests"]
        self.assertEqual(requests["read"]["effective"], {"nearest": "view", "higher": "view"})
        self.assertEqual(requests["write"]["effective"], {"nearest": "change", "higher": "view"})
        self.assertContains(resp, 'id="cv-ancestor-policy"')
        self.assertNotContains(resp, "cv_guardian_parent_permission")
        self.assertNotContains(resp, "cv_guardian_parent_create_permission")

        # a nested manage page passes ancestry first: no view grant on the document, no page
        resp = self.client.get(reverse("note-manage", kwargs={"document_pk": self.alice_doc.pk}))
        self.assertEqual(resp.status_code, 403)


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


class GuardianSeedEditShareTest(TestCase):
    """The seed shares one of bob's documents with alice: she may edit it, not delete it."""

    def setUp(self):
        from django.core.management import call_command

        call_command("seed")
        User = get_user_model()
        self.alice = User.objects.get(username="alice")
        self.bob = User.objects.get(username="bob")
        self.doc = Document.objects.get(title="Release Checklist")

    def test_owned_by_bob(self):
        self.assertEqual(self.doc.owner, self.bob)

    def test_alice_can_view_and_edit(self):
        self.client.force_login(self.alice)
        self.assertContains(self.client.get(reverse("document-list")), "Release Checklist")
        self.assertEqual(self.client.get(reverse("document-update", kwargs={"pk": self.doc.pk})).status_code, 200)

    def test_alice_cannot_delete(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(reverse("document-delete", kwargs={"pk": self.doc.pk})).status_code, 403)

    def test_bob_has_full_rights(self):
        self.client.force_login(self.bob)
        for key in ("document-detail", "document-update", "document-delete"):
            self.assertEqual(self.client.get(reverse(key, kwargs={"pk": self.doc.pk})).status_code, 200, key)


class GuardianSeedNotesTest(TestCase):
    """The seed adds notes under two documents; the document grants gate them, the note grants stay separate."""

    def setUp(self):
        from django.core.management import call_command

        call_command("seed")
        User = get_user_model()
        self.alice = User.objects.get(username="alice")
        self.bob = User.objects.get(username="bob")
        self.handbook = Document.objects.get(title="Team Handbook")
        self.checklist = Document.objects.get(title="Release Checklist")

    def test_seed_twice_keeps_note_count(self):
        from django.core.management import call_command

        count = Note.objects.count()
        self.assertGreater(count, 0)
        call_command("seed")
        self.assertEqual(Note.objects.count(), count)

    def test_bob_reads_handbook_notes_but_cannot_add(self):
        self.client.force_login(self.bob)
        kwargs = {"document_pk": self.handbook.pk}
        resp = self.client.get(reverse("note-list", kwargs=kwargs))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "onboarding")
        self.assertContains(self.client.get(reverse("note-list", kwargs=kwargs), HTTP_ACCEPT_LANGUAGE="de"), "Notizen")
        self.assertEqual(self.client.get(reverse("note-create", kwargs=kwargs)).status_code, 403)

    def test_alice_may_add_notes_to_release_checklist(self):
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("note-create", kwargs={"document_pk": self.checklist.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_note_gates_stay_independent(self):
        bobs_note = Note.objects.get(document=self.checklist, text__startswith="Tag the release")
        alices_note = Note.objects.get(document=self.checklist, text="Changelog reviewed.")
        # alice may change the document but holds only view on bob's note
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("note-update", kwargs={"document_pk": self.checklist.pk, "pk": bobs_note.pk}))
        self.assertEqual(resp.status_code, 403)
        # the document owner gets change on every note of his document
        self.client.force_login(self.bob)
        resp = self.client.get(reverse("note-update", kwargs={"document_pk": self.checklist.pk, "pk": alices_note.pk}))
        self.assertEqual(resp.status_code, 200)
