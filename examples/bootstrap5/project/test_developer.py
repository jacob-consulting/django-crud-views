from io import StringIO
from unittest.mock import patch

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from crud_views.lib.settings import crud_views_settings
from project import seeding


class DeveloperSeedTest(TestCase):
    def test_seed_creates_regular_developer(self):
        output = StringIO()
        call_command("seed", stdout=output)
        self.assertTrue(get_user_model().objects.filter(username="developer").exists())
        call_command("seed", stdout=output)
        developer = get_user_model().objects.get(username="developer")
        self.assertTrue(developer.is_active)
        self.assertFalse(developer.is_staff)
        self.assertFalse(developer.is_superuser)
        self.assertTrue(self.client.login(username="developer", password="developer"))
        self.assertEqual(developer.groups.get().name, crud_views_settings.manage_group)
        self.assertFalse(
            Group.objects.get(name=crud_views_settings.manage_group).user_set.exclude(pk=developer.pk).exists()
        )
        self.assertIn("developer/developer", output.getvalue())
        perms = developer.get_all_permissions()
        expected = """
            library.view_author library.view_book library.view_contract
            nested.view_company nested.view_department nested.view_employee nested.view_office
            formsets.view_questionnaire formsets.view_question formsets.view_choice
            formsets.view_checklist formsets.view_checklistitem workflow.view_campaign
            polymorphic_demo.view_vehicle polymorphic_demo.view_car polymorphic_demo.view_truck
            polymorphic_demo.view_motorcycle guardian_demo.view_document guardian_demo.view_note
            object_detail.view_supplier object_detail.view_warehouse object_detail.view_tag object_detail.view_product
            breadcrumbs.view_workspace breadcrumbs.view_board conditional.view_registration conditional.view_event
            conditional.view_session conditional.view_speaker conditional.view_customer
            formsets_conditional.view_conference formsets_conditional.view_session formsets_conditional.view_speaker
            custom_form.view_contact context_buttons.view_ticket action_menus.view_chore action_menus.view_step
            label_modes.view_gadget flash_messages.view_notice disabled_actions.view_ticket
            delete_demo.view_project delete_demo.view_task delete_demo.view_milestone resources.view_s3file
        """
        self.assertEqual(perms, set(expected.split()))
        self.assertTrue(all(perm.split(".")[1].startswith("view_") for perm in perms))
        self.assertIn("resources.view_s3file", perms)

    def test_custom_group_preserves_members_and_legitimate_reads(self):
        group = Group.objects.create(name="Example developers")
        perm = Permission.objects.get(content_type__app_label="library", codename="view_author")
        group.permissions.add(perm)
        other = get_user_model().objects.create_user(username="other")
        other.groups.add(group)
        with patch.object(crud_views_settings, "manage_group", group.name):
            call_command("seed", stdout=StringIO())
        self.assertEqual(set(group.user_set.values_list("username", flat=True)), {"developer", "other"})
        self.assertEqual(list(group.permissions.all()), [perm])

    def test_rejects_customized_identity_without_resetting_password(self):
        for flag in ("is_staff", "is_superuser", "is_active"):
            with self.subTest(flag=flag):
                user = get_user_model().objects.create_user(
                    username="developer", password="custom", **{flag: flag != "is_active"}
                )
                with self.assertRaisesRegex(CommandError, "developer.*" + flag):
                    seeding.ensure_demo_users()
                user.refresh_from_db()
                self.assertTrue(user.check_password("custom"))
                self.assertEqual(getattr(user, flag), flag != "is_active")
                user.delete()

    def test_conflicting_model_permissions_are_preserved_and_named(self):
        for source in ("direct", "existing-group", "configured-group"):
            with self.subTest(source=source):
                user = get_user_model().objects.create_user(username="developer")
                perm = Permission.objects.get(content_type__app_label="library", codename="change_author")
                if source == "direct":
                    relation = user.user_permissions
                    expected = "developer"
                else:
                    expected = crud_views_settings.manage_group if source == "configured-group" else "writers"
                    group, _ = Group.objects.get_or_create(name=expected)
                    if source == "existing-group":
                        user.groups.add(group)
                    relation = group.permissions
                relation.add(perm)
                with self.assertRaisesRegex(CommandError, expected + ".*library.change_author"):
                    seeding.ensure_developer_read_access(user)
                self.assertTrue(relation.filter(pk=perm.pk).exists())
                self.assertFalse(user.user_permissions.filter(codename="view_author").exists())
                relation.remove(perm)
                user.delete()

    def test_inspection_uses_fresh_relations_and_leaves_permission_caches_empty(self):
        user = get_user_model().objects.create_user(username="developer")
        user = get_user_model().objects.prefetch_related("user_permissions", "groups__permissions").get(pk=user.pk)
        seeding.ensure_developer_read_access(user)
        for attr in ("_perm_cache", "_user_perm_cache", "_group_perm_cache"):
            self.assertFalse(hasattr(user, attr))
        self.assertTrue(user.has_perm("library.view_author"))
        self.assertTrue(user.has_perm("resources.view_s3file"))

    def test_seed_model_conflict_preserves_private_credentials_and_memberships(self):
        user = get_user_model().objects.create_user(username="developer", password="private-password")
        original_password = user.password
        group = Group.objects.create(name="Existing readers")
        user.groups.add(group)
        perm = Permission.objects.get(content_type__app_label="library", codename="change_author")
        user.user_permissions.add(perm)

        with self.assertRaisesRegex(CommandError, "developer.*library.change_author"):
            call_command("seed", stdout=StringIO())

        self.assertIsNone(authenticate(username="developer", password="developer"))
        self.assertIsNotNone(authenticate(username="developer", password="private-password"))
        user.refresh_from_db()
        self.assertEqual(user.password, original_password)
        self.assertEqual(list(user.groups.all()), [group])
        self.assertEqual(list(user.user_permissions.all()), [perm])
        self.assertTrue(user.has_perm("library.change_author"))
        self.assertFalse(Group.objects.filter(name=crud_views_settings.manage_group).exists())
        self.assertFalse(get_user_model().objects.filter(username__in=("alice", "bob")).exists())

    def test_seed_group_object_conflict_leaves_no_new_public_account(self):
        from guardian.shortcuts import assign_perm, get_perms
        from guardian_demo.models import Document
        from library.models import Author

        owner = get_user_model().objects.create_user(username="alice", password="private-alice")
        original_password = owner.password
        document = Document.objects.create(title="Roadmap 2027", body="Operator content", owner=owner)
        group = Group.objects.create(name="Example developers")
        owner.groups.add(group)
        assign_perm("guardian_demo.change_document", group, document)

        with (
            patch.object(crud_views_settings, "manage_group", group.name),
            self.assertRaisesRegex(CommandError, "guardian_demo.Document.*change_document"),
        ):
            call_command("seed", stdout=StringIO())

        self.assertIsNone(authenticate(username="developer", password="developer"))
        self.assertFalse(get_user_model().objects.filter(username="developer").exists())
        self.assertFalse(get_user_model().objects.filter(username="bob").exists())
        self.assertEqual(list(group.user_set.all()), [owner])
        self.assertEqual(set(get_perms(group, document)), {"change_document"})
        self.assertTrue(get_user_model().objects.get(pk=owner.pk).has_perm("guardian_demo.change_document", document))
        owner.refresh_from_db()
        self.assertEqual(owner.password, original_password)
        self.assertFalse(owner.user_permissions.exists())
        self.assertFalse(Author.objects.exists())
        document.refresh_from_db()
        self.assertEqual(document.body, "Operator content")
        self.assertEqual(document.owner_id, owner.pk)
        self.assertEqual(Document.objects.count(), 1)

    def test_seed_late_object_conflict_rolls_back_earlier_feature_changes(self):
        from delete_demo.models import Milestone, Project, Task
        from guardian.shortcuts import assign_perm, get_perms
        from guardian_demo.models import Document
        from library.models import Author
        from workflow.models import Campaign

        owner = get_user_model().objects.create_user(username="alice", password="private-alice")
        user = get_user_model().objects.create_user(username="developer", password="private-password")
        original_passwords = {actor.pk: actor.password for actor in (owner, user)}
        group = Group.objects.create(name="Existing readers")
        user.groups.add(group)
        project = Project.objects.create(title="Old prototype", owner=owner)
        milestone = Milestone.objects.create(project=project, title="Clickable mockup")
        assign_perm("delete_demo.change_milestone", user, milestone)

        with self.assertRaisesRegex(CommandError, "delete_demo.Milestone.*change_milestone"):
            call_command("seed", stdout=StringIO())

        self.assertIsNone(authenticate(username="developer", password="developer"))
        self.assertIsNotNone(authenticate(username="developer", password="private-password"))
        for actor in (owner, user):
            actor.refresh_from_db()
            self.assertEqual(actor.password, original_passwords[actor.pk])
            self.assertFalse(actor.user_permissions.exists())
        self.assertEqual(list(user.groups.all()), [group])
        self.assertFalse(Group.objects.filter(name=crud_views_settings.manage_group).exists())
        self.assertFalse(get_user_model().objects.filter(username="bob").exists())
        self.assertEqual(set(get_perms(user, milestone)), {"change_milestone"})
        self.assertTrue(user.has_perm("delete_demo.change_milestone", milestone))
        self.assertEqual(list(Project.objects.all()), [project])
        self.assertEqual(list(Milestone.objects.all()), [milestone])
        for model in (Author, Campaign, Document, Task):
            with self.subTest(model=model.__name__):
                self.assertFalse(model.objects.exists())

    def test_prefetched_relations_do_not_hide_later_conflicts(self):
        user = get_user_model().objects.create_user(username="developer")
        group = Group.objects.create(name="writers")
        user.groups.add(group)
        user = get_user_model().objects.prefetch_related("user_permissions", "groups__permissions").get(pk=user.pk)
        perm = Permission.objects.get(content_type__app_label="library", codename="delete_author")
        group.permissions.add(perm)
        with self.assertRaisesRegex(CommandError, "writers.*library.delete_author"):
            seeding.ensure_developer_read_access(user)
        self.assertTrue(group.permissions.filter(pk=perm.pk).exists())


@override_settings(DEBUG=False)
class DeveloperAccessTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed", stdout=StringIO())

    def setUp(self):
        self.client.force_login(get_user_model().objects.get(username="developer"))

    def test_ordinary_reads_and_production_diagnostics(self):
        from library.models import Author
        from nested.models import Company, Department

        company = Company.objects.first()
        department = Department.objects.filter(company=company).first()
        urls = [
            reverse("author-list"),
            reverse("author-detail", kwargs={"pk": Author.objects.first().pk}),
            reverse("author-manage"),
            reverse("department-list", kwargs={"company_pk": company.pk}),
            reverse("employee-list", kwargs={"company_pk": company.pk, "department_pk": department.pk}),
            reverse("department-manage", kwargs={"company_pk": company.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_resource_reads_and_mutations_denied(self):
        from resources.views import FAKE_BUCKET, S3File, S3FileTouchView

        before = [dict(row) for row in FAKE_BUCKET]
        self.assertEqual(self.client.get(reverse("s3file-list")).status_code, 200)
        for row in before:
            kwargs = {"pk": S3File.model_validate(row).key_md5}
            self.assertEqual(self.client.get(reverse("s3file-detail", kwargs=kwargs)).status_code, 200)
            with patch.object(S3FileTouchView, "action") as action:
                for key in ("delete", "touch"):
                    self.assertEqual(self.client.post(reverse(f"s3file-{key}", kwargs=kwargs)).status_code, 403)
                action.assert_not_called()
        self.assertEqual(FAKE_BUCKET, before)

    def test_application_writes_denied_without_effects(self):
        from custom_form.models import Contact
        from flash_messages.views import NoticeComposeView
        from formsets.models import Choice, Question, Questionnaire
        from library.models import Author
        from workflow.models import Campaign

        models = (Author, Questionnaire, Question, Choice, Contact, Campaign)
        before = {model: list(model.objects.order_by("pk").values()) for model in models}
        author = Author.objects.first()
        questionnaire = Questionnaire.objects.first()
        contact = Contact.objects.first()
        campaign = Campaign.objects.first()
        cases = [
            ("author-create", None, {"first_name": "Forbidden", "last_name": "Writer"}),
            ("author-update", {"pk": author.pk}, {"first_name": "Forbidden", "last_name": "Writer"}),
            ("author-delete", {"pk": author.pk}, {}),
            ("questionnaire-create", None, {"title": "Forbidden"}),
            ("questionnaire-update", {"pk": questionnaire.pk}, {"title": "Forbidden"}),
            ("campaign-workflow", {"pk": campaign.pk}, {"transition": "wf_activate"}),
            ("contact-remind", {"pk": contact.pk}, {"note": "Forbidden"}),
            ("contact-invite", None, {"email": "forbidden@example.com"}),
            ("notice-compose", None, {"level": "success", "text": "Forbidden"}),
        ]
        with patch.object(NoticeComposeView, "cv_form_valid") as compose:
            for name, kwargs, data in cases:
                with self.subTest(name=name):
                    self.assertEqual(self.client.post(reverse(name, kwargs=kwargs), data).status_code, 403)
            compose.assert_not_called()
        self.assertEqual({model: list(model.objects.order_by("pk").values()) for model in models}, before)
