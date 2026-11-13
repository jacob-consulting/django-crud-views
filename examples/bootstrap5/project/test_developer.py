from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command, CommandError
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
        self.assertFalse(Group.objects.get(name=crud_views_settings.manage_group).user_set.exclude(pk=developer.pk).exists())
        self.assertIn("developer/developer", output.getvalue())
        perms = developer.get_all_permissions()
        self.assertEqual(len(perms), 47)
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
            reverse("author-list"), reverse("author-detail", kwargs={"pk": Author.objects.first().pk}),
            reverse("author-manage"), reverse("department-list", kwargs={"company_pk": company.pk}),
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
        from formsets.models import Questionnaire, Question, Choice
        from library.models import Author
        from workflow.models import Campaign
        from flash_messages.views import NoticeComposeView

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
