from unittest.mock import patch

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase
from django.urls import reverse
from project.testing import form_payload

from crud_views.lib.conditional import ConditionalGroup, QuerysetConditions, ToggleGroup
from queryset_conditional.models import RequestBatch, Service, ServiceCategory, ServiceRequest
from queryset_conditional.standalone import RequestCreateView, RequestForm, RequestUpdateView

# Deliberately unmatched data belongs to test fixtures, never the seeded live demo.
PERMISSIVE = QuerysetConditions(
    "service", conditional_key="conditional_category", keys=("on_site", "remote", "general"), allow_unmatched=True
)


class PermissiveRequestForm(RequestForm):
    cv_conditional_groups = [
        ConditionalGroup(toggle=PERMISSIVE.when("on_site"), fields=["visit_address"]),
        ConditionalGroup(toggle=PERMISSIVE.when("remote"), fields=["meeting_url"]),
    ]

    def get_layout_fields(self):
        return [
            "service",
            ToggleGroup(PERMISSIVE.when("on_site"), "visit_address"),
            ToggleGroup(PERMISSIVE.when("remote"), "meeting_url"),
        ]


class RestrictedRequestForm(RequestForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = self.fields["service"].queryset.filter(category__code="on_site")


class StandaloneRequestTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="request-admin", password="pw")
        cls.on_site = ServiceCategory.objects.create(code="on_site")
        cls.remote = ServiceCategory.objects.create(code="remote")
        cls.general = ServiceCategory.objects.create(code="general")
        cls.boiler = Service.objects.create(name="Boiler inspection", category=cls.on_site)
        cls.appliance = Service.objects.create(name="Appliance installation", category=cls.on_site)
        cls.consultation = Service.objects.create(name="Technical consultation", category=cls.remote)
        cls.review = Service.objects.create(name="Document review", category=cls.general)

    def setUp(self):
        self.client.force_login(self.admin)

    def test_authenticated_create_page_renders(self):
        response = self.client.get("/queryset-conditional/service-request/create/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="service"')
        self.assertContains(response, 'cv-data-toggle-kind="queryset"', count=2)

    def test_native_option_labels_and_real_navbar_render(self):
        response = self.client.get(reverse("service-request-create"))
        for service in (self.boiler, self.appliance, self.consultation, self.review):
            self.assertContains(response, f'value="{service.pk}">{service.name}</option>')
        for name in ("home", "logout", "set_language", "conference-list", "customer-list"):
            self.assertContains(response, reverse(name))

    def test_on_site_choices_save_and_reopen(self):
        for service in (self.boiler, self.appliance):
            with self.subTest(service=service.name):
                create_url = reverse("service-request-create")
                payload = form_payload(self.client.get(create_url))
                payload.update(
                    service=service.pk, visit_address="12 Example Street", meeting_url="invalid inactive URL"
                )
                response = self.client.post(create_url, payload)
                self.assertEqual(response.status_code, 302)
                saved = ServiceRequest.objects.get(service=service)
                self.assertIsNone(saved.batch_id)
                self.assertEqual(saved.visit_address, "12 Example Street")
                self.assertEqual(saved.meeting_url, "")
                reopened = self.client.get(reverse("service-request-update", kwargs={"pk": saved.pk}))
                self.assertEqual(reopened.status_code, 200)
                self.assertEqual(form_payload(reopened)["visit_address"], "12 Example Street")

    def test_switch_remote_then_general_clears_saved_fields(self):
        saved = ServiceRequest.objects.create(service=self.boiler, visit_address="Old address")
        url = reverse("service-request-update", kwargs={"pk": saved.pk})
        payload = form_payload(self.client.get(url))
        payload.update(service=self.consultation.pk, meeting_url="https://example.com/meeting")
        self.assertEqual(self.client.post(url, payload).status_code, 302)
        saved.refresh_from_db()
        self.assertEqual(
            (saved.service_id, saved.visit_address, saved.meeting_url),
            (self.consultation.pk, "", "https://example.com/meeting"),
        )
        payload = form_payload(self.client.get(url))
        self.assertEqual(payload["meeting_url"], "https://example.com/meeting")
        payload.update(service=self.review.pk, visit_address="Forged address", meeting_url="invalid inactive URL")
        self.assertEqual(self.client.post(url, payload).status_code, 302)
        saved.refresh_from_db()
        self.assertEqual((saved.service_id, saved.visit_address, saved.meeting_url), (self.review.pk, "", ""))
        reopened = form_payload(self.client.get(url))
        self.assertEqual((reopened["visit_address"], reopened["meeting_url"]), ("", ""))

    def test_active_fields_required_and_url_validation_preserved(self):
        self.assertIsInstance(RequestForm(cv_view=None).fields["meeting_url"], forms.URLField)
        cases = (
            (self.boiler, "visit_address", ""),
            (self.appliance, "visit_address", ""),
            (self.consultation, "meeting_url", ""),
            (self.consultation, "meeting_url", "not a URL"),
        )
        for service, field, value in cases:
            with self.subTest(service=service.name, value=value):
                response = self.client.post(reverse("service-request-create"), {"service": service.pk, field: value})
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
        self.assertEqual(ServiceRequest.objects.count(), 0)

    def test_invalid_or_blank_selection_cannot_save(self):
        for value in ("", "not-a-key", 999999):
            with self.subTest(value=value):
                response = self.client.post(
                    reverse("service-request-create"), {"service": value, "conditional_category": "general"}
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn("service", response.context["form"].errors)
        self.assertEqual(ServiceRequest.objects.count(), 0)

    def test_strict_unmatched_render_and_post_are_diagnosable(self):
        unknown = ServiceCategory.objects.create(code="unknown")
        service = Service.objects.create(name="Unknown service", category=unknown)
        url = reverse("service-request-create")
        with self.assertRaisesMessage(ImproperlyConfigured, "unmatched category 'unknown'"):
            self.client.get(url)
        response = self.client.post(url, {"service": service.pk, "visit_address": "Forged"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("service", response.context["form"].errors)
        self.assertContains(response, "unknown")
        self.assertEqual(ServiceRequest.objects.count(), 0)

    def test_category_change_after_get_is_checked_on_post(self):
        url = reverse("service-request-create")
        payload = form_payload(self.client.get(url))
        self.on_site.code = "changed"
        self.on_site.save()
        payload.update(service=self.boiler.pk, visit_address="12 Example Street")
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("service", response.context["form"].errors)
        self.assertEqual(ServiceRequest.objects.count(), 0)

    def test_permissive_fixture_renders_and_saves_unknown_with_empty_fields(self):
        unknown = ServiceCategory.objects.create(code="unknown")
        service = Service.objects.create(name="Unknown service", category=unknown)
        with patch.object(RequestCreateView, "form_class", PermissiveRequestForm):
            url = reverse("service-request-create")
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            payload = form_payload(response)
            payload.update(service=service.pk, visit_address="Discarded", meeting_url="not a URL")
            self.assertEqual(self.client.post(url, payload).status_code, 302)
        saved = ServiceRequest.objects.get()
        self.assertEqual((saved.service_id, saved.visit_address, saved.meeting_url), (service.pk, "", ""))
        with patch.object(RequestUpdateView, "form_class", PermissiveRequestForm):
            reopened = self.client.get(reverse("service-request-update", kwargs={"pk": saved.pk}))
            self.assertEqual(reopened.status_code, 200)
            self.assertEqual(form_payload(reopened)["visit_address"], "")
            self.assertEqual(form_payload(reopened)["meeting_url"], "")

    def test_restricted_queryset_rejects_forged_selection(self):
        with patch.object(RequestCreateView, "form_class", RestrictedRequestForm):
            url = reverse("service-request-create")
            response = self.client.get(url)
            self.assertNotContains(response, self.consultation.name)
            response = self.client.post(url, {"service": self.consultation.pk, "meeting_url": "https://example.com"})
            self.assertEqual(response.status_code, 200)
            self.assertIn("service", response.context["form"].errors)
        self.assertEqual(ServiceRequest.objects.count(), 0)

    def test_unused_and_unoffered_categories_do_not_block_render(self):
        ServiceCategory.objects.create(code="unused")
        self.assertEqual(self.client.get(reverse("service-request-create")).status_code, 200)
        Service.objects.filter(category=self.remote).delete()
        self.assertEqual(self.client.get(reverse("service-request-create")).status_code, 200)

    def test_native_labels_have_constant_query_cost(self):
        for count in (2, 20):
            with self.subTest(count=count):
                Service.objects.all().delete()
                Service.objects.bulk_create(
                    [Service(name=f"Service {number}", category=self.on_site) for number in range(count)]
                )
                form = RequestForm(cv_view=None)
                with self.assertNumQueries(1):
                    markup = str(form["service"])
                self.assertEqual(markup.count("<option "), count + 1)
                objects = list(form.fields["service"].queryset)
                with self.assertNumQueries(0):
                    self.assertEqual([str(obj) for obj in objects], [obj.name for obj in objects])

    def test_list_renders_saved_requests(self):
        ServiceRequest.objects.create(service=self.boiler, visit_address="12 Example Street")
        response = self.client.get(reverse("service-request-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Boiler inspection")
        self.assertContains(response, "12 Example Street")

    def test_models_belong_to_the_new_app(self):
        for model in (ServiceCategory, Service, RequestBatch, ServiceRequest):
            self.assertEqual(model._meta.app_label, "queryset_conditional")
        batch = RequestBatch.objects.create(title="Weekly visits")
        request = ServiceRequest.objects.create(batch=batch, service=self.boiler)
        self.assertEqual(list(batch.requests.all()), [request])

    def test_initial_migration_creates_all_owned_models(self):
        loader = MigrationLoader(connection)
        migration = ("queryset_conditional", "0001_initial")
        self.assertIn(migration, loader.applied_migrations)
        state = loader.project_state([migration])
        self.assertEqual(
            {name for app, name in state.models if app == "queryset_conditional"},
            {"servicecategory", "service", "requestbatch", "servicerequest"},
        )

    def test_anonymous_and_unprivileged_users_cannot_access_views(self):
        saved = ServiceRequest.objects.create(service=self.boiler, visit_address="Original")
        urls = [
            reverse("service-request-list"),
            reverse("service-request-create"),
            reverse("service-request-update", kwargs={"pk": saved.pk}),
        ]
        self.client.logout()
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 302)
        user = get_user_model().objects.create_user(username="no-permissions")
        self.client.force_login(user)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403)
        for url in urls[1:]:
            self.assertEqual(self.client.post(url, {"service": self.review.pk}).status_code, 403)
        saved.refresh_from_db()
        self.assertEqual(saved.visit_address, "Original")
        self.assertEqual(ServiceRequest.objects.count(), 1)

    def test_explicit_model_permissions_allow_create_and_update(self):
        user = get_user_model().objects.create_user(username="request-editor")
        user.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="queryset_conditional",
                codename__in=["view_servicerequest", "add_servicerequest", "change_servicerequest"],
            )
        )
        self.client.force_login(user)
        url = reverse("service-request-create")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.post(url, {"service": self.review.pk}).status_code, 302)
        saved = ServiceRequest.objects.get()
        url = reverse("service-request-update", kwargs={"pk": saved.pk})
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(
            self.client.post(url, {"service": self.boiler.pk, "visit_address": "Allowed"}).status_code, 302
        )
        saved.refresh_from_db()
        self.assertEqual(saved.visit_address, "Allowed")
