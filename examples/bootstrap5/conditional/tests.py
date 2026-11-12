from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from project.testing import field_key, form_payload

from conditional.models import Event, Registration, Session, Speaker


class ConditionalTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")

    def setUp(self):
        self.client.force_login(self.admin)


class RegistrationConditionalGroupTest(ConditionalTestCase):
    def test_list_renders_with_snippets(self):
        Registration.objects.create(name="Jane Doe")
        resp = self.client.get(reverse("registration-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Jane Doe")
        self.assertContains(resp, "snippet-panels")

    def test_create_without_company_leaves_company_fields_blank(self):
        resp = self.client.get(reverse("registration-create"))
        payload = form_payload(resp)
        payload["name"] = "Jane Doe"
        resp = self.client.post(reverse("registration-create"), payload)
        self.assertEqual(resp.status_code, 302)
        registration = Registration.objects.get(name="Jane Doe")
        self.assertFalse(registration.with_company)
        self.assertIsNone(registration.company_name)

    def test_create_with_company_requires_company_name(self):
        resp = self.client.get(reverse("registration-create"))
        payload = form_payload(resp)
        payload["name"] = "Acme Attendee"
        payload["with_company"] = "on"
        resp = self.client.post(reverse("registration-create"), payload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("company_name", resp.context["form"].errors)

    def test_create_with_company_success(self):
        resp = self.client.get(reverse("registration-create"))
        payload = form_payload(resp)
        payload["name"] = "Acme Attendee"
        payload["with_company"] = "on"
        payload["company_name"] = "Acme Corp"
        resp = self.client.post(reverse("registration-create"), payload)
        self.assertEqual(resp.status_code, 302)
        registration = Registration.objects.get(name="Acme Attendee")
        self.assertEqual(registration.company_name, "Acme Corp")

    def test_detail_page_renders(self):
        registration = Registration.objects.create(name="Jane Doe", with_company=True, company_name="Acme Corp")
        resp = self.client.get(reverse("registration-detail", kwargs={"pk": registration.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Jane Doe")
        self.assertContains(resp, "Acme Corp")

    def test_create_page_renders_toggle_ui(self):
        resp = self.client.get(reverse("registration-create"))
        self.assertContains(resp, "cv-data-toggle-group")
        self.assertContains(resp, 'cv-data-toggle-field="with_company"')
        self.assertContains(resp, "Company details")

    def test_ui_toggle_on_saves_note(self):
        # add_note is a UIFieldToggle: a transient checkbox injected by the mixin,
        # not a model field.
        resp = self.client.get(reverse("registration-create"))
        payload = form_payload(resp)
        payload["name"] = "Note Taker"
        payload["add_note"] = "on"
        payload["note"] = "Vegetarian lunch, please."
        resp = self.client.post(reverse("registration-create"), payload)
        self.assertEqual(resp.status_code, 302)
        registration = Registration.objects.get(name="Note Taker")
        self.assertEqual(registration.note, "Vegetarian lunch, please.")

    def test_ui_toggle_off_clears_note_on_update(self):
        registration = Registration.objects.create(name="Note Loser", note="old note")
        url = reverse("registration-update", kwargs={"pk": registration.pk})
        resp = self.client.get(url)
        payload = form_payload(resp)
        payload.pop("add_note", None)
        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 302)
        registration.refresh_from_db()
        self.assertIsNone(registration.note)

    def test_ui_toggle_initial_checked_when_note_exists(self):
        # UIFieldToggle is not persisted — the form must derive its initial state
        # from the instance, otherwise updating an object with a note would
        # render the toggle off and silently clear the note on save.
        registration = Registration.objects.create(name="Note Keeper", note="keep me")
        resp = self.client.get(reverse("registration-update", kwargs={"pk": registration.pk}))
        self.assertTrue(resp.context["form"]["add_note"].value())

    def test_toggle_off_clears_company_fields(self):
        registration = Registration.objects.create(
            name="Toggle Test", with_company=True, company_name="Old Co", vat_id="X1"
        )
        url = reverse("registration-update", kwargs={"pk": registration.pk})
        resp = self.client.get(url)
        payload = form_payload(resp)
        payload.pop("with_company", None)
        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 302)
        registration.refresh_from_db()
        self.assertFalse(registration.with_company)
        self.assertIsNone(registration.company_name)


class EventConditionalFormsetTest(ConditionalTestCase):
    def test_create_with_sessions_off_skips_formset(self):
        resp = self.client.get(reverse("event-create"))
        payload = form_payload(resp)
        payload["name"] = "Simple Meetup"
        # with_sessions checkbox not in payload => off
        resp = self.client.post(reverse("event-create"), payload)
        self.assertEqual(resp.status_code, 302)
        event = Event.objects.get(name="Simple Meetup")
        self.assertEqual(event.sessions.count(), 0)

    def test_create_with_sessions_on_validates_formset(self):
        resp = self.client.get(reverse("event-create"))
        payload = form_payload(resp)
        payload["name"] = "Annual Conference"
        payload["with_sessions"] = "on"
        payload[field_key(payload, "-title")] = "Opening Keynote"
        resp = self.client.post(reverse("event-create"), payload)
        self.assertEqual(
            resp.status_code,
            302,
            getattr(resp, "context", None) and str(resp.context.get("form") and resp.context["form"].errors),
        )
        event = Event.objects.get(name="Annual Conference")
        self.assertTrue(event.sessions.filter(title="Opening Keynote").exists())

    def test_detail_page_renders_session_count(self):
        event = Event.objects.create(name="Counted", with_sessions=True)
        Session.objects.create(event=event, title="Only Session")
        resp = self.client.get(reverse("event-detail", kwargs={"pk": event.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Counted")
        self.assertContains(resp, "1")

    def test_toggle_off_skips_existing_speakers(self):
        # The speakers formset uses on_off="skip" (the safe default): untoggling
        # hides the formset but existing rows survive the save — contrast with
        # sessions' on_off="purge" below.
        event = Event.objects.create(name="Keeps Speakers", with_speakers=True)
        Speaker.objects.create(event=event, name="Ada Lovelace")

        url = reverse("event-update", kwargs={"pk": event.pk})
        resp = self.client.get(url)
        payload = form_payload(resp)
        payload.pop("with_speakers", None)

        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 302)
        event.refresh_from_db()
        self.assertFalse(event.with_speakers)
        self.assertEqual(event.speakers.count(), 1)  # skip: rows untouched

    def test_create_with_speakers_on_validates_formset(self):
        resp = self.client.get(reverse("event-create"))
        payload = form_payload(resp)
        payload["name"] = "Speaker Summit"
        payload["with_speakers"] = "on"
        payload[field_key(payload, "-name")] = "Grace Hopper"
        resp = self.client.post(reverse("event-create"), payload)
        self.assertEqual(resp.status_code, 302)
        event = Event.objects.get(name="Speaker Summit")
        self.assertTrue(event.speakers.filter(name="Grace Hopper").exists())

    def test_toggle_off_purges_existing_sessions(self):
        event = Event.objects.create(name="To Purge", with_sessions=True)
        Session.objects.create(event=event, title="Existing Session")

        url = reverse("event-update", kwargs={"pk": event.pk})
        resp = self.client.get(url)
        payload = form_payload(resp)
        payload.pop("with_sessions", None)

        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 302)
        event.refresh_from_db()
        self.assertFalse(event.with_sessions)
        self.assertEqual(event.sessions.count(), 0)


class ConditionalSeedTest(TestCase):
    def test_seed_twice(self):
        from django.core.management import call_command

        call_command("seed")
        counts = (
            Registration.objects.count(),
            Event.objects.count(),
            Session.objects.count(),
            Speaker.objects.count(),
        )
        call_command("seed")
        self.assertEqual(
            (
                Registration.objects.count(),
                Event.objects.count(),
                Session.objects.count(),
                Speaker.objects.count(),
            ),
            counts,
        )
        self.assertGreater(Registration.objects.count(), 0)
        self.assertGreater(Speaker.objects.count(), 0)


class CustomerCrudTest(ConditionalTestCase):
    def test_create_routes_render_native_widgets(self):
        from django.urls import get_resolver
        from lxml import html

        self.assertTrue(
            all(f"customer-{key}" in get_resolver().reverse_dict for key in ("create", "radio_create")),
            "Both Customer create routes must be registered",
        )
        for key, selector in (("create", "select[name=kind]"), ("radio_create", "input[type=radio][name=kind]")):
            with self.subTest(editor=key):
                response = self.client.get(reverse(f"customer-{key}"))
                self.assertEqual(response.status_code, 200)
                document = html.fromstring(response.content)
                controls = document.cssselect(selector)
                self.assertEqual(len(controls), 1 if key == "create" else 3)
                self.assertEqual(len(document.cssselect("[cv-data-toggle-group]")), 4)
                for legend in ("Consumer preferences", "Business details", "Wholesale terms", "Distribution details"):
                    self.assertContains(response, legend)

    def test_editors_share_declarations_and_layout(self):
        from conditional.views import CustomerForm, CustomerRadioForm

        self.assertIs(CustomerForm.cv_conditional_groups, CustomerRadioForm.cv_conditional_groups)
        self.assertIs(CustomerForm.get_layout_fields, CustomerRadioForm.get_layout_fields)
        self.assertEqual(len(CustomerForm.cv_conditional_groups), 4)

    def test_both_editors_create_all_three_options(self):
        from conditional.models import Customer

        for editor in ("create", "radio_create"):
            for kind in ("consumer", "wholesale", "distributor"):
                with self.subTest(editor=editor, kind=kind):
                    url = reverse(f"customer-{editor}")
                    payload = form_payload(self.client.get(url))
                    name = f"{editor}-{kind}"
                    payload.update(
                        name=name,
                        kind=kind,
                        consumer_note="Preference",
                        company="Shared Co",
                        price_tier="B",
                        payment_terms="net60",
                        wholesale_terms="0",
                        distribution_region="North",
                    )
                    response = self.client.post(url, payload)
                    self.assertEqual(response.status_code, 302)
                    customer = Customer.objects.get(name=name)
                    self.assertEqual(customer.kind, kind)
                    self.assertEqual(customer.consumer_note, "Preference" if kind == "consumer" else None)
                    self.assertEqual(customer.company, None if kind == "consumer" else "Shared Co")
                    self.assertEqual(customer.price_tier, None if kind == "consumer" else "B")
                    self.assertEqual(customer.payment_terms, "unset" if kind == "consumer" else "net60")
                    self.assertEqual(customer.wholesale_terms, 0 if kind == "wholesale" else None)
                    self.assertEqual(customer.distribution_region, "North" if kind == "distributor" else "")

    def test_shared_retention_then_clearing_persists_and_reopens(self):
        from lxml import html

        from conditional.models import Customer

        for editor in ("update", "radio_update"):
            with self.subTest(editor=editor):
                customer = Customer.objects.create(
                    name=editor,
                    kind="wholesale",
                    company="Shared Co",
                    price_tier="B",
                    payment_terms="net30",
                    wholesale_terms=60,
                )
                url = reverse(f"customer-{editor}", kwargs={"pk": customer.pk})
                payload = form_payload(self.client.get(url))
                payload.update(kind="distributor", distribution_region="West", wholesale_terms="forged")
                self.assertEqual(self.client.post(url, payload).status_code, 302)
                customer.refresh_from_db()
                self.assertEqual(
                    (customer.company, customer.price_tier, customer.payment_terms), ("Shared Co", "B", "net30")
                )
                self.assertIsNone(customer.wholesale_terms)
                self.assertEqual(customer.distribution_region, "West")
                reopened = self.client.get(url)
                self.assertEqual(reopened.context["form"]["kind"].value(), "distributor")
                self.assertIsNone(reopened.context["form"]["wholesale_terms"].value())
                payload = form_payload(reopened)
                payload.update(kind="consumer", consumer_note="Keep this")
                self.assertEqual(self.client.post(url, payload).status_code, 302)
                customer.refresh_from_db()
                self.assertEqual(customer.name, editor)
                self.assertEqual(customer.consumer_note, "Keep this")
                self.assertIsNone(customer.company)
                self.assertIsNone(customer.price_tier)
                self.assertEqual(customer.payment_terms, "unset")
                self.assertIsNone(customer.wholesale_terms)
                self.assertEqual(customer.distribution_region, "")
                reopened = self.client.get(url)
                self.assertIsNone(reopened.context["form"]["price_tier"].value())
                self.assertEqual(reopened.context["form"]["payment_terms"].value(), "unset")
                detail = self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk}))
                self.assertEqual(detail.status_code, 200)
                detail_text = html.fromstring(detail.content).text_content()
                for visible in (editor, "Keep this", "None", "unset", '"" (blank)'):
                    self.assertIn(visible, detail_text)

    def test_inactive_omitted_and_forged_values_clear_defaults(self):
        from conditional.models import Customer

        for editor in ("create", "radio_create"):
            for forged in (False, True):
                with self.subTest(editor=editor, forged=forged):
                    name = f"{editor}-{forged}"
                    payload = {"name": name, "kind": "consumer"}
                    if forged:
                        payload.update(
                            company="forged",
                            price_tier="forged",
                            payment_terms="forged",
                            wholesale_terms="forged",
                            distribution_region="forged",
                        )
                    self.assertEqual(self.client.post(reverse(f"customer-{editor}"), payload).status_code, 302)
                    customer = Customer.objects.get(name=name)
                    self.assertIsNone(customer.company)
                    self.assertIsNone(customer.price_tier)
                    self.assertIsNone(customer.wholesale_terms)
                    self.assertEqual(customer.payment_terms, "unset")
                    self.assertEqual(customer.distribution_region, "")

    def test_invalid_active_fields_and_controller_never_save(self):
        from conditional.models import Customer

        for editor in ("update", "radio_update"):
            customer = Customer.objects.create(name=editor, kind="consumer", consumer_note="Saved")
            url = reverse(f"customer-{editor}", kwargs={"pk": customer.pk})
            before = Customer.objects.values().get(pk=customer.pk)
            for kind, required in (
                ("wholesale", {"company", "price_tier", "wholesale_terms"}),
                ("distributor", {"company", "price_tier", "distribution_region"}),
                ("invalid", {"kind"}),
                ("", {"kind"}),
            ):
                with self.subTest(editor=editor, kind=kind):
                    response = self.client.post(url, {"name": "Changed", "kind": kind, "payment_terms": "unset"})
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(required <= response.context["form"].errors.keys())
                    self.assertEqual(Customer.objects.values().get(pk=customer.pk), before)

    def test_permission_checks_cover_both_editors(self):
        from project.seeding import grant_model_perms

        from conditional.models import Customer

        customer = Customer.objects.create(name="Protected")
        user = get_user_model().objects.create_user(username="ordinary")
        self.client.force_login(user)
        for action in ("create", "radio_create", "update", "radio_update"):
            kwargs = {"pk": customer.pk} if "update" in action else {}
            url = reverse(f"customer-{action}", kwargs=kwargs)
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, {"name": "Forged", "kind": "consumer"}).status_code, 403)
        self.assertEqual(Customer.objects.count(), 1)
        customer.refresh_from_db()
        self.assertEqual(customer.name, "Protected")
        grant_model_perms(user, Customer)
        for action in ("create", "radio_create", "update", "radio_update"):
            kwargs = {"pk": customer.pk} if "update" in action else {}
            url = reverse(f"customer-{action}", kwargs=kwargs)
            self.assertEqual(self.client.get(url).status_code, 200)
            self.assertEqual(self.client.post(url, {"name": "Granted", "kind": "consumer"}).status_code, 302)

    def test_radio_posts_retain_csrf_protection(self):
        from django.test import Client

        from conditional.models import Customer

        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        customer = Customer.objects.create(name="Protected")
        for action in ("radio_create", "radio_update"):
            kwargs = {"pk": customer.pk} if action == "radio_update" else {}
            response = client.post(reverse(f"customer-{action}", kwargs=kwargs), {"kind": "consumer"})
            self.assertEqual(response.status_code, 403)


class CustomerDiscoveryTest(ConditionalTestCase):
    def test_customer_seeds_are_coherent_idempotent_and_preserve_edits(self):
        from django.core.management import call_command

        from conditional.models import Customer

        call_command("seed")
        self.assertEqual(Customer.objects.count(), 3)
        consumer = Customer.objects.get(name="Consumer Customer")
        wholesale = Customer.objects.get(name="Wholesale Customer")
        distributor = Customer.objects.get(name="Distributor Customer")
        self.assertEqual(consumer.kind, "consumer")
        self.assertTrue(consumer.consumer_note)
        self.assertIsNone(consumer.company)
        self.assertIsNone(consumer.price_tier)
        self.assertEqual(consumer.payment_terms, "unset")
        self.assertIsNone(consumer.wholesale_terms)
        self.assertEqual(consumer.distribution_region, "")
        for customer in (wholesale, distributor):
            self.assertIsNone(customer.consumer_note)
            self.assertTrue(customer.company)
            self.assertIn(customer.price_tier, ("A", "B"))
            self.assertIn(customer.payment_terms, ("net30", "net60"))
        self.assertEqual(wholesale.kind, "wholesale")
        self.assertIn(wholesale.wholesale_terms, (0, 30, 60))
        self.assertEqual(wholesale.distribution_region, "")
        self.assertEqual(distributor.kind, "distributor")
        self.assertIsNone(distributor.wholesale_terms)
        self.assertTrue(distributor.distribution_region)
        consumer.consumer_note = "An existing user edit"
        consumer.save()
        before = list(Customer.objects.values())
        old_counts = (
            Registration.objects.count(),
            Event.objects.count(),
            Session.objects.count(),
            Speaker.objects.count(),
        )
        call_command("seed")
        self.assertEqual(list(Customer.objects.values()), before)
        self.assertEqual(
            (Registration.objects.count(), Event.objects.count(), Session.objects.count(), Speaker.objects.count()),
            old_counts,
        )

    def test_landing_and_customer_pages_link_to_real_editors_and_old_examples(self):
        from urllib.parse import urlsplit

        from lxml import html

        from conditional.models import Customer

        customer = Customer.objects.create(name="Discoverable")
        landing = self.client.get(reverse("registration-list"))
        self.assertContains(landing, "Choice-driven customers")
        self.assertIn(reverse("customer-list"), html.fromstring(landing.content).xpath("//a/@href"))
        for key in ("list", "detail", "create", "radio_create", "update", "radio_update", "delete"):
            with self.subTest(page=key):
                kwargs = {"pk": customer.pk} if key in ("detail", "update", "radio_update", "delete") else {}
                response = self.client.get(reverse(f"customer-{key}", kwargs=kwargs))
                self.assertEqual(response.status_code, 200)
                links = html.fromstring(response.content).xpath("//a/@href")
                for old_key in ("registration-list", "event-list"):
                    self.assertIn(reverse(old_key), links)
                    self.assertEqual(self.client.get(reverse(old_key)).status_code, 200)
                if key == "delete":
                    continue
                actions = ("update", "radio_update") if kwargs else ("create", "radio_create")
                for action in actions:
                    target = reverse(f"customer-{action}", kwargs=kwargs)
                    rendered_targets = [link for link in links if urlsplit(link).path == target]
                    self.assertTrue(rendered_targets, f"No rendered link to {target}")
                    self.assertEqual(self.client.get(rendered_targets[0]).status_code, 200)
                for text in ("Dropdown", "Radio", "shared business details", "before saving", "unset", "None"):
                    self.assertContains(response, text)

    def test_demo_users_can_read_add_and_change_with_both_editors(self):
        from django.core.management import call_command

        from conditional.models import Customer

        call_command("seed")
        for username in ("alice", "bob"):
            user = get_user_model().objects.get(username=username)
            self.assertFalse(user.is_superuser)
            self.assertTrue(
                user.has_perms(["conditional.view_customer", "conditional.add_customer", "conditional.change_customer"])
            )
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse("customer-list")).status_code, 200)
            for create_key, update_key in (("create", "update"), ("radio_create", "radio_update")):
                with self.subTest(username=username, editor=create_key):
                    name = f"{username}-{create_key}"
                    payload = {"name": name, "kind": "consumer", "consumer_note": "Saved"}
                    self.assertEqual(self.client.post(reverse(f"customer-{create_key}"), payload).status_code, 302)
                    customer = Customer.objects.get(name=name)
                    kwargs = {"pk": customer.pk}
                    self.assertEqual(self.client.get(reverse("customer-detail", kwargs=kwargs)).status_code, 200)
                    payload["consumer_note"] = "Updated"
                    self.assertEqual(
                        self.client.post(reverse(f"customer-{update_key}", kwargs=kwargs), payload).status_code, 302
                    )
                    customer.refresh_from_db()
                    self.assertEqual(customer.consumer_note, "Updated")
