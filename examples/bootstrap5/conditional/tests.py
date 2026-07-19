from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from conditional.models import Event, Registration, Session, Speaker
from project.testing import field_key, form_payload


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
