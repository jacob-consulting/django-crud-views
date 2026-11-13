import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase
from django.urls import reverse
from lxml import html
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


class DocumentationRecipeTests(TestCase):
    def render_copied_wrapper(self, form, legend=None):
        import re

        from django.template import Context, Template
        from test_docs_sync import DOCS_DIR

        section = (DOCS_DIR / "reference/conditional.md").read_text().split("### Copied conditional wrapper", 1)[1]
        recipe = re.search(r"```django\n(.*?)^```", section, re.S | re.M).group(1)
        template = Template(recipe)
        layout = form.get_layout_fields()
        for field in layout:
            if isinstance(field, ToggleGroup):
                field.legend = legend
        with (
            patch.object(form, "get_layout_fields", return_value=layout),
            patch(
                "crud_views.lib.conditional.layout.render_to_string",
                side_effect=lambda name, context: template.render(Context(context)),
            ),
        ):
            return self.render(form)

    def test_copied_wrapper_empty_membership_hides_and_disables_in_browser(self):
        form_class = self.recipe("queryset-matching")["RequestForm"]
        root = Path(__file__).resolve().parents[3]
        script = """
const fs = require('node:fs');
const assert = require('node:assert/strict');
const {JSDOM} = require('jsdom');
const dom = new JSDOM('<form>' + JSON.parse(fs.readFileSync(0, 'utf8')) + '</form>', {runScripts: 'outside-only'});
dom.window.eval(fs.readFileSync('src/crud_views/static/crud_views/js/toggle.js', 'utf8'));
dom.window.cv.initConditional(dom.window.document);
const groups = [...dom.window.document.querySelectorAll('[cv-data-toggle-group]')];
assert.equal(groups.length, 2);
for (const group of groups) {
    assert.equal(group.getAttribute('cv-data-toggle-values'), '[]');
    assert.equal(group.style.display, 'none');
    assert.equal(group.querySelector('input').disabled, true);
}
dom.window.close();
"""
        for legend in (None, 'Details <"&>'):
            with self.subTest(legend=legend):
                form = form_class(cv_view=None, prefix='row-<"&>')
                form.fields["service"].queryset = form.fields["service"].queryset.none()
                markup = self.render_copied_wrapper(form, legend)
                result = subprocess.run(
                    ["node", "-e", script], input=json.dumps(markup), text=True, capture_output=True, cwd=root
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_copied_wrapper_successful_no_fields_guard_emits_no_container(self):
        form = self.recipe("queryset-no-fields")["NoFieldsRequestForm"](cv_view=None)
        rendered = html.fromstring(self.render_copied_wrapper(form))
        self.assertFalse(rendered.xpath("//*[@cv-data-toggle-group]"))
        self.assertFalse(rendered.xpath("//*[@role='alert']"))

    def test_copied_wrapper_bound_coverage_diagnostic_is_escaped_outside_groups(self):
        category = ServiceCategory.objects.create(code="<script>alert(1)</script>")
        service = Service.objects.create(name="Unknown category", category=category)
        for recipe, name in (("queryset-matching", "RequestForm"), ("queryset-no-fields", "NoFieldsRequestForm")):
            with self.subTest(recipe=recipe):
                form = self.recipe(recipe)[name](data={"service": service.pk}, cv_view=None)
                self.assertFalse(form.is_valid())
                rendered = html.fromstring(self.render_copied_wrapper(form))
                diagnostics = rendered.xpath("//*[@class='cv-queryset-condition-error'][@role='alert']")
                self.assertTrue(diagnostics)
                for diagnostic in diagnostics:
                    self.assertIn(category.code, diagnostic.text_content())
                    self.assertFalse(diagnostic.xpath("ancestor::*[@cv-data-toggle-group]"))
                self.assertFalse(rendered.xpath("//script"))

    def render(self, form):
        from crispy_forms.helper import FormHelper
        from crispy_forms.layout import Layout
        from crispy_forms.utils import render_crispy_form

        # Render the documented layout explicitly without view-owned Save/Cancel actions.
        helper = FormHelper()
        helper.form_tag = False
        helper.layout = Layout(*form.get_layout_fields())
        return render_crispy_form(form, helper=helper)

    def recipe(self, name):
        from test_docs_sync import conditional_recipe

        return conditional_recipe(name)

    def test_published_strict_permissive_and_category_change_recipe(self):
        recipe = self.recipe("queryset-matching")
        strict = recipe["RequestForm"]
        permissive = recipe["PermissiveRequestForm"]
        category = ServiceCategory.objects.create(code="general")
        service = Service.objects.create(name="Document review", category=category)
        form = strict(data={"service": service.pk, "visit_address": "discard", "meeting_url": "invalid"}, cv_view=None)
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        self.assertEqual((saved.visit_address, saved.meeting_url), ("", ""))
        self.assertIn("Document review", self.render(strict(cv_view=None)))
        category.code = "new-category"
        category.save()
        # No preceding GET is needed, and a category changed after GET is equally rejected.
        rejected = strict(data={"service": service.pk}, cv_view=None)
        self.assertFalse(rejected.is_valid())
        self.assertIn("service", rejected.errors)
        self.assertIn("new-category", self.render(rejected))
        with self.assertRaisesMessage(ImproperlyConfigured, "new-category"):
            self.render(strict(cv_view=None))
        allowed = permissive(
            data={"service": service.pk, "visit_address": "discard", "meeting_url": "invalid"}, cv_view=None
        )
        self.assertTrue(allowed.is_valid(), allowed.errors)
        self.assertEqual((allowed.save().visit_address, allowed.instance.meeting_url), ("", ""))
        self.assertIn("Document review", self.render(permissive(cv_view=None)))

    def test_published_all_no_fields_guard_and_empty_queryset(self):
        form_class = self.recipe("queryset-no-fields")["NoFieldsRequestForm"]
        category = ServiceCategory.objects.create(code="general")
        service = Service.objects.create(name="Document review", category=category)
        self.assertIn("Document review", self.render(form_class(cv_view=None)))
        valid = form_class(data={"service": service.pk}, cv_view=None)
        self.assertTrue(valid.is_valid(), valid.errors)
        category.code = "unknown"
        category.save()
        with self.assertRaisesMessage(ImproperlyConfigured, "unknown"):
            self.render(form_class(cv_view=None))
        invalid = form_class(data={"service": service.pk}, cv_view=None)
        self.assertFalse(invalid.is_valid())
        self.assertIn("service", invalid.errors)
        empty = form_class(cv_view=None)
        empty.fields["service"].queryset = empty.fields["service"].queryset.none()
        options = html.fromstring(self.render(empty)).xpath("//select[@name='service']/option/@value")
        self.assertEqual(options, [""])

    def test_published_recipe_zero_matching_options_and_restricted_queryset(self):
        recipe = self.recipe("queryset-matching")
        category = ServiceCategory.objects.create(code="general")
        service = Service.objects.create(name="Document review", category=category)
        markup = self.render(recipe["RequestForm"](cv_view=None))
        self.assertEqual(markup.count('cv-data-toggle-values="[]"'), 2)
        restricted = recipe["RestrictedRequestForm"](data={"service": service.pk}, cv_view=None)
        self.assertFalse(restricted.is_valid())
        self.assertIn("service", restricted.errors)


class FeatureSeedTests(TestCase):
    def test_feature_is_registered_and_seed_is_idempotent(self):
        from importlib import import_module

        from project.features import FEATURES

        features = [feature for feature in FEATURES if feature.app == "queryset_conditional"]
        self.assertEqual(len(features), 1)
        feature = features[0]
        self.assertEqual(feature.url_name, "service_request-list")
        self.assertEqual(feature.group, "forms")
        self.assertEqual(feature.docs[0].anchor, "kind-1-conditional-field-group-in-a-form")
        for username in ("alice", "bob"):
            get_user_model().objects.create_user(username=username)
        seed = import_module(f"{feature.app}.seed").seed
        seed()
        seed()
        self.assertEqual(ServiceCategory.objects.count(), 3)
        self.assertEqual(Service.objects.count(), 4)
        self.assertEqual(Service.objects.filter(category__code="on_site").count(), 2)
        self.assertEqual(set(ServiceCategory.objects.values_list("code", flat=True)), {"on_site", "remote", "general"})
        self.assertEqual(RequestBatch.objects.count(), 1)
        self.assertEqual(ServiceRequest.objects.filter(batch__isnull=True).count(), 1)
        self.assertEqual(ServiceRequest.objects.filter(batch__isnull=False).count(), 3)
        self.assertEqual(
            set(ServiceRequest.objects.filter(batch__isnull=False).values_list("service__category__code", flat=True)),
            {"on_site", "remote", "general"},
        )
        for username in ("alice", "bob"):
            user = get_user_model().objects.get(username=username)
            self.assertTrue(user.has_perm("queryset_conditional.add_servicerequest"))
            self.assertTrue(user.has_perm("queryset_conditional.change_requestbatch"))
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse(feature.url_name)).status_code, 200)
            for request in ServiceRequest.objects.all():
                form = RequestForm(
                    data={
                        "service": request.service_id,
                        "visit_address": request.visit_address,
                        "meeting_url": request.meeting_url,
                    },
                    instance=request,
                    cv_view=None,
                )
                self.assertTrue(form.is_valid(), form.errors)


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
        response = self.client.get(reverse("service_request-create"))
        for service in (self.boiler, self.appliance, self.consultation, self.review):
            self.assertContains(response, f'value="{service.pk}">{service.name}</option>')
        for name in ("home", "logout", "set_language", "conference-list", "customer-list"):
            self.assertContains(response, reverse(name))

    def test_on_site_choices_save_and_reopen(self):
        for service in (self.boiler, self.appliance):
            with self.subTest(service=service.name):
                create_url = reverse("service_request-create")
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
                reopened = self.client.get(reverse("service_request-update", kwargs={"pk": saved.pk}))
                self.assertEqual(reopened.status_code, 200)
                self.assertEqual(form_payload(reopened)["visit_address"], "12 Example Street")

    def test_switch_remote_then_general_clears_saved_fields(self):
        saved = ServiceRequest.objects.create(service=self.boiler, visit_address="Old address")
        url = reverse("service_request-update", kwargs={"pk": saved.pk})
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
                response = self.client.post(reverse("service_request-create"), {"service": service.pk, field: value})
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
        self.assertEqual(ServiceRequest.objects.count(), 0)

    def test_invalid_or_blank_selection_cannot_save(self):
        for value in ("", "not-a-key", 999999):
            with self.subTest(value=value):
                response = self.client.post(
                    reverse("service_request-create"), {"service": value, "conditional_category": "general"}
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn("service", response.context["form"].errors)
        self.assertEqual(ServiceRequest.objects.count(), 0)

    def test_strict_unmatched_render_and_post_are_diagnosable(self):
        unknown = ServiceCategory.objects.create(code="unknown")
        service = Service.objects.create(name="Unknown service", category=unknown)
        url = reverse("service_request-create")
        with self.assertRaisesMessage(ImproperlyConfigured, "unmatched category 'unknown'"):
            self.client.get(url)
        response = self.client.post(url, {"service": service.pk, "visit_address": "Forged"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("service", response.context["form"].errors)
        self.assertContains(response, "unknown")
        self.assertEqual(ServiceRequest.objects.count(), 0)

    def test_category_change_after_get_is_checked_on_post(self):
        url = reverse("service_request-create")
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
            url = reverse("service_request-create")
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            payload = form_payload(response)
            payload.update(service=service.pk, visit_address="Discarded", meeting_url="not a URL")
            self.assertEqual(self.client.post(url, payload).status_code, 302)
        saved = ServiceRequest.objects.get()
        self.assertEqual((saved.service_id, saved.visit_address, saved.meeting_url), (service.pk, "", ""))
        with patch.object(RequestUpdateView, "form_class", PermissiveRequestForm):
            reopened = self.client.get(reverse("service_request-update", kwargs={"pk": saved.pk}))
            self.assertEqual(reopened.status_code, 200)
            self.assertEqual(form_payload(reopened)["visit_address"], "")
            self.assertEqual(form_payload(reopened)["meeting_url"], "")

    def test_restricted_queryset_rejects_forged_selection(self):
        with patch.object(RequestCreateView, "form_class", RestrictedRequestForm):
            url = reverse("service_request-create")
            response = self.client.get(url)
            self.assertNotContains(response, f'value="{self.consultation.pk}">{self.consultation.name}</option>')
            response = self.client.post(url, {"service": self.consultation.pk, "meeting_url": "https://example.com"})
            self.assertEqual(response.status_code, 200)
            self.assertIn("service", response.context["form"].errors)
        self.assertEqual(ServiceRequest.objects.count(), 0)

    def test_unused_and_unoffered_categories_do_not_block_render(self):
        ServiceCategory.objects.create(code="unused")
        self.assertEqual(self.client.get(reverse("service_request-create")).status_code, 200)
        Service.objects.filter(category=self.remote).delete()
        self.assertEqual(self.client.get(reverse("service_request-create")).status_code, 200)

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
        response = self.client.get(reverse("service_request-list"))
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
            reverse("service_request-list"),
            reverse("service_request-create"),
            reverse("service_request-update", kwargs={"pk": saved.pk}),
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
        url = reverse("service_request-create")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.post(url, {"service": self.review.pk}).status_code, 302)
        saved = ServiceRequest.objects.get()
        url = reverse("service_request-update", kwargs={"pk": saved.pk})
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(
            self.client.post(url, {"service": self.boiler.pk, "visit_address": "Allowed"}).status_code, 302
        )
        saved.refresh_from_db()
        self.assertEqual(saved.visit_address, "Allowed")


class BatchRequestTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from queryset_conditional.seed import seed

        for username in ("alice", "bob"):
            get_user_model().objects.create_user(username=username)
        seed()
        cls.editor = get_user_model().objects.get(username="alice")
        cls.boiler = Service.objects.get(name="Boiler inspection")
        cls.remote = Service.objects.get(name="Technical consultation")
        cls.general = Service.objects.get(name="Document review")

    def setUp(self):
        self.client.force_login(self.editor)

    variants = ("service_batch", "service_batch_compact")

    def page_payload(self, variant, batch=None):
        url = reverse(f"{variant}-update", kwargs={"pk": batch.pk}) if batch else reverse(f"{variant}-create")
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        payload = form_payload(page)
        total_key = next(key for key in payload if key.endswith("-TOTAL_FORMS"))
        return url, page, payload, total_key.removesuffix("-TOTAL_FORMS")

    def fragment_params(self, page):
        content = html.fromstring(page.content).cssselect(".cv-formset-content")[0]
        data = json.loads(content.get("cv-data-formset"))
        return {
            "template": "|".join(data["hierarchy"]),
            "pk": data["prefix_key"].rsplit("-", 2)[-2],
            "num": form_payload(page)[f"{content.get('cv-data-formset-prefix')}-TOTAL_FORMS"],
            "formset_parent_prefix_key": data["parent_prefix_key"],
        }

    def test_batch_create_routes_render_both_layouts(self):
        self.assertEqual(self.client.get("/queryset-conditional/service-batch/create/").status_code, 200)
        for path in ("service-batch", "service-batch-compact"):
            with self.subTest(path=path):
                page = self.client.get(f"/queryset-conditional/{path}/create/")
                self.assertEqual(page.status_code, 200)
                document = html.fromstring(page.content)
                if path.endswith("compact"):
                    self.assertTrue(document.cssselect(".cv-formset-row-compact"))
                    self.assertTrue(document.cssselect(".cv-formset-compact-fields"))
                else:
                    self.assertFalse(document.cssselect(".cv-formset-row-compact"))
                    self.assertContains(page, 'cv-data-toggle-kind="queryset"', count=2)

    def test_create_no_js_and_reopen_independent_rows(self):
        for variant in self.variants:
            with self.subTest(variant=variant):
                url, _, payload, prefix = self.page_payload(variant)
                payload.update(
                    {
                        "title": variant,
                        f"{prefix}-TOTAL_FORMS": "3",
                        f"{prefix}-0-service": self.boiler.pk,
                        f"{prefix}-0-visit_address": "On site",
                        f"{prefix}-0-meeting_url": "invalid inactive URL",
                        f"{prefix}-1-service": self.remote.pk,
                        f"{prefix}-1-visit_address": "Forged inactive address",
                        f"{prefix}-1-meeting_url": "https://example.com/call",
                    }
                )
                self.assertEqual(self.client.post(url, payload).status_code, 302)
                batch = RequestBatch.objects.get(title=variant)
                self.assertEqual(batch.requests.count(), 2)  # Empty extra row stays empty.
                self.assertEqual(batch.requests.get(service=self.boiler).meeting_url, "")
                self.assertEqual(batch.requests.get(service=self.remote).visit_address, "")
                _, _, saved, prefix = self.page_payload(variant, batch)
                self.assertEqual(saved[f"{prefix}-0-visit_address"], "On site")
                self.assertEqual(saved[f"{prefix}-1-meeting_url"], "https://example.com/call")
                self.assertEqual(self.client.get(reverse(f"{variant}-list")).status_code, 200)

    def test_active_url_validation_and_invalid_sibling_prevent_all_writes(self):
        for variant in self.variants:
            for invalid_url in ("", "not a URL"):
                with self.subTest(variant=variant, invalid_url=invalid_url):
                    batch = RequestBatch.objects.create(title="Unchanged")
                    row = ServiceRequest.objects.create(batch=batch, service=self.boiler, visit_address="Original")
                    url, _, payload, prefix = self.page_payload(variant, batch)
                    payload.update(
                        {
                            "title": "Must not save",
                            f"{prefix}-TOTAL_FORMS": "2",
                            f"{prefix}-0-visit_address": "Must not save",
                            f"{prefix}-1-service": self.remote.pk,
                            f"{prefix}-1-meeting_url": invalid_url,
                        }
                    )
                    response = self.client.post(url, payload)
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(html.fromstring(response.content).cssselect(".invalid-feedback"))
                    row.refresh_from_db()
                    batch.refresh_from_db()
                    self.assertEqual(
                        (batch.title, row.visit_address, batch.requests.count()), ("Unchanged", "Original", 1)
                    )

    def test_invalid_parent_prevents_row_changes(self):
        for variant in self.variants:
            batch = RequestBatch.objects.create(title=variant)
            row = ServiceRequest.objects.create(batch=batch, service=self.boiler, visit_address="Original")
            url, _, payload, prefix = self.page_payload(variant, batch)
            payload.update({"title": "", f"{prefix}-0-visit_address": "Must not save"})
            self.assertEqual(self.client.post(url, payload).status_code, 200)
            row.refresh_from_db()
            self.assertEqual(row.visit_address, "Original")

    def test_update_add_delete_and_unchanged_cleanup(self):
        for variant in self.variants:
            with self.subTest(variant=variant):
                batch = RequestBatch.objects.create(title=variant)
                cleanup = ServiceRequest.objects.create(batch=batch, service=self.general, visit_address="Stale")
                deleted = ServiceRequest.objects.create(batch=batch, service=self.remote, meeting_url="invalid")
                url, page, payload, prefix = self.page_payload(variant, batch)
                fragment = self.client.get(url, self.fragment_params(page))
                self.assertEqual(fragment.status_code, 200)
                self.assertIn(f'name="{prefix}-3-service"', fragment.json()["html"])
                payload.update(
                    {
                        f"{prefix}-TOTAL_FORMS": "4",
                        f"{prefix}-1-DELETE": "on",
                        f"{prefix}-3-service": self.remote.pk,
                        f"{prefix}-3-meeting_url": "https://example.com/added",
                    }
                )
                self.assertEqual(self.client.post(url, payload).status_code, 302)
                cleanup.refresh_from_db()
                self.assertEqual(cleanup.visit_address, "")
                self.assertFalse(ServiceRequest.objects.filter(pk=deleted.pk).exists())
                self.assertEqual(batch.requests.count(), 2)
                self.assertEqual(batch.requests.get(service=self.remote).meeting_url, "https://example.com/added")

    def test_strict_bound_redisplay_rejects_changed_category(self):
        for variant in self.variants:
            url, _, payload, prefix = self.page_payload(variant)
            category = ServiceCategory.objects.create(code=f"unknown_{variant}")
            unknown = Service.objects.create(name="Unconfigured", category=category)
            payload.update({"title": "Reject", f"{prefix}-0-service": unknown.pk})
            response = self.client.post(url, payload)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, category.code)
            self.assertFalse(RequestBatch.objects.filter(title="Reject").exists())
            unknown.delete()

    def test_foreign_row_identity_is_rejected(self):
        for variant in self.variants:
            batch = RequestBatch.objects.create(title=variant)
            owned = ServiceRequest.objects.create(batch=batch, service=self.boiler, visit_address="Owned")
            foreign = ServiceRequest.objects.filter(batch__isnull=False).exclude(batch=batch).first()
            original = (foreign.service_id, foreign.visit_address, foreign.meeting_url)
            url, _, payload, prefix = self.page_payload(variant, batch)
            payload[f"{prefix}-0-id"] = foreign.pk
            response = self.client.post(url, payload)
            self.assertEqual(response.status_code, 200)
            foreign.refresh_from_db()
            owned.refresh_from_db()
            self.assertEqual((foreign.service_id, foreign.visit_address, foreign.meeting_url), original)
            self.assertEqual(owned.visit_address, "Owned")

    def test_permissions_protect_pages_fragments_and_posts(self):
        unauthorized = get_user_model().objects.create_user(username="unauthorized-batch")
        batch = RequestBatch.objects.first()
        before = list(ServiceRequest.objects.values_list("pk", "service_id", "visit_address", "meeting_url"))
        for variant in self.variants:
            for target in (None, batch):
                self.client.force_login(self.editor)
                url, page, payload, _ = self.page_payload(variant, target)
                params = self.fragment_params(page)
                for user, expected in ((None, 302), (unauthorized, 403)):
                    self.client.logout()
                    if user:
                        self.client.force_login(user)
                    self.assertEqual(self.client.get(url).status_code, expected)
                    self.assertEqual(self.client.get(url, params).status_code, expected)
                    self.assertEqual(self.client.post(url, payload).status_code, expected)
        self.assertEqual(
            list(ServiceRequest.objects.values_list("pk", "service_id", "visit_address", "meeting_url")), before
        )


class SourceAndNavigationTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser(username="source-admin", password="pw"))

    def test_standalone_source_has_shared_definitions_and_own_editor(self):
        page = self.client.get(reverse("service_request-create"))
        self.assertContains(page, "queryset_conditional/conditions.py")
        self.assertContains(page, "queryset_conditional/standalone.py")
        self.assertNotContains(page, "queryset_conditional/inlines.py")

    def test_all_pages_show_only_relevant_source_and_active_navigation(self):
        from project.tests import ACTIVE_NAV_GROUP, ACTIVE_NAV_ITEM, navbar_html

        category = ServiceCategory.objects.create(code="general")
        service = Service.objects.create(name="General", category=category)
        request = ServiceRequest.objects.create(service=service)
        batch = RequestBatch.objects.create(title="Source example")
        for variant, obj, module in (
            ("service_request", request, "standalone.py"),
            ("service_batch", batch, "inlines.py"),
            ("service_batch_compact", batch, "inlines.py"),
        ):
            for action in ("list", "create", "update"):
                with self.subTest(variant=variant, action=action):
                    page = self.client.get(
                        reverse(f"{variant}-{action}", kwargs={"pk": obj.pk} if action == "update" else None)
                    )
                    self.assertEqual(page.status_code, 200)
                    document = html.fromstring(page.content)
                    panels = document.cssselect('[id^="snippet-queryset_conditional-"]')
                    self.assertEqual(
                        [panel.get("id") for panel in panels],
                        [
                            f"snippet-queryset_conditional-{name.replace('.', '-')}"
                            for name in ("models.py", "conditions.py", module)
                        ],
                    )
                    sources = "\n".join(panel.text_content() for panel in panels)
                    self.assertIn("SERVICE_CONDITIONS", sources)
                    self.assertIn("class RequestForm" if module == "standalone.py" else "class RequestRowForm", sources)
                    for unrelated in ("Conference", "Questionnaire", "Customer", "formsets_conditional"):
                        self.assertNotIn(unrelated, sources)
                    nav = navbar_html(page)
                    self.assertEqual(ACTIVE_NAV_GROUP.findall(nav), ["forms"])
                    self.assertEqual(ACTIVE_NAV_ITEM.findall(nav), [reverse(f"{variant}-list")])
                    for name in ("service_request", "service_batch", "service_batch_compact"):
                        self.assertIn(reverse(f"{name}-list"), nav)

    def test_explicit_selection_rejects_absolute_and_traversal_paths(self):
        from project.templatetags.example_tags import snippet_panels

        view = RequestCreateView()
        for path in ("../project/settings.py", "/etc/passwd", "nested/../../project/settings.py"):
            with (
                self.subTest(path=path),
                patch.object(view, "example_source_files", (path,), create=True),
                self.assertRaisesMessage(ValueError, "example_source_files"),
            ):
                snippet_panels({"view": view})

    def test_explicit_selection_rejects_symlink_escape(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from project.templatetags.example_tags import snippet_panels

        view = RequestCreateView()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            app = root / "queryset_conditional"
            app.mkdir()
            outside = root / "private.py"
            outside.write_text("private secret")
            (app / "escape.py").symlink_to(outside)
            with (
                self.settings(BASE_DIR=root),
                patch.object(view, "example_source_files", ("escape.py",), create=True),
                self.assertRaisesMessage(ValueError, "example_source_files"),
            ):
                snippet_panels({"view": view})

    def test_explicit_selection_is_complete_and_does_not_append_templates(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from project.templatetags.example_tags import snippet_panels

        view = RequestCreateView()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            app = root / "queryset_conditional"
            (app / "templates").mkdir(parents=True)
            (app / "models.py").write_text("class Relevant: pass")
            (app / "views.py").write_text("class Unrelated: pass")
            (app / "templates" / "other.html").write_text("Unrelated template")
            with self.settings(BASE_DIR=root), patch.object(view, "example_source_files", ("models.py",), create=True):
                result = snippet_panels({"view": view})
            self.assertEqual([panel["title"] for panel in result["panels"]], ["queryset_conditional/models.py"])

    def test_default_source_selection_retains_python_and_template_panels(self):
        from pathlib import Path

        from django.conf import settings
        from project.templatetags.example_tags import SNIPPET_FILES, snippet_panels
        from theming.views import ThemeIndexView

        view = ThemeIndexView()
        result = snippet_panels({"view": view})
        app = Path(settings.BASE_DIR) / "theming"
        expected = [f"theming/{name}" for name in SNIPPET_FILES if (app / name).exists()]
        python_count = len(expected)
        expected += [
            f"theming/{path.relative_to(app).as_posix()}" for path in sorted((app / "templates").rglob("*.html"))
        ]
        self.assertGreater(len(expected), python_count)
        self.assertEqual([panel["title"] for panel in result["panels"]], expected)
