import json

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from lxml import html
from project.testing import field_key, field_keys, form_payload

from formsets_conditional.models import Conference, Session, Speaker


class FormsetsConditionalTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")

    def setUp(self):
        self.client.force_login(self.admin)


def _speaker_prefix(payload: dict) -> str:
    """The management-form prefix of the (single) nested speakers formset."""
    key = next(k for k in field_keys(payload, "-TOTAL_FORMS") if "speakers" in k)
    return key[: -len("-TOTAL_FORMS")]


class ConferenceTest(FormsetsConditionalTestCase):
    def assert_session_and_speaker_frames(self, content, fragment=False):
        document = html.fromstring(content)
        rows = document.cssselect(".cv-formset-row")
        self.assertTrue(rows)
        for row in rows:
            key = json.loads(row.get("cv-data-formset-form"))["key"]
            cards = row.cssselect(":scope > .cv-formset-row-card")
            self.assertEqual(bool(cards), key == "sessions")
            self.assertFalse("cv-formset-row-compact" in row.classes)
        if not fragment:
            self.assertTrue(document.cssselect('[cv-data-formset-key="sessions"]'))
            self.assertTrue(document.cssselect('[cv-data-formset-key="sessions-speakers"]'))

    def test_plain_speaker_update_fragment_and_invalid_response(self):
        conference = Conference.objects.create(name="Frames", with_sessions=True)
        session = Session.objects.create(conference=conference, title="Framed session")
        speaker = Speaker.objects.create(session=session, name="Unchanged speaker")
        url = reverse("conference-update", kwargs={"pk": conference.pk})
        initial = self.client.get(url)
        self.assert_session_and_speaker_frames(initial.content)
        document = html.fromstring(initial.content)
        content = document.cssselect('[cv-data-formset-key="sessions-speakers"] .cv-formset-content')[0]
        data = json.loads(content.get("cv-data-formset"))
        payload = form_payload(initial)
        fragment = self.client.get(
            url,
            {
                "template": "|".join(data["hierarchy"]),
                "pk": data["prefix_key"].rsplit("-", 2)[-2],
                "num": payload[f"{content.get('cv-data-formset-prefix')}-TOTAL_FORMS"],
                "formset_parent_prefix_key": data["parent_prefix_key"],
            },
        )
        self.assertEqual(fragment.status_code, 200)
        self.assert_session_and_speaker_frames(fragment.json()["html"], fragment=True)
        name = next(key for key in field_keys(payload, "-name") if payload[key] == speaker.name)
        payload[name] = ""
        invalid = self.client.post(url, payload)
        self.assertContains(invalid, "This field is required")
        self.assert_session_and_speaker_frames(invalid.content)
        speaker.refresh_from_db()
        self.assertEqual(speaker.name, "Unchanged speaker")
        payload[name] = "Corrected speaker"
        self.assertEqual(self.client.post(url, payload).status_code, 302)
        speaker.refresh_from_db()
        self.assertEqual(speaker.name, "Corrected speaker")
        self.assert_session_and_speaker_frames(self.client.get(url).content)

    def test_list_renders_with_snippets(self):
        Conference.objects.create(name="PyCon")
        resp = self.client.get(reverse("conference-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "PyCon")
        self.assertContains(resp, "snippet-panels")

    def test_create_with_billing_sessions_and_speakers(self):
        resp = self.client.get(reverse("conference-create"))
        self.assertEqual(resp.status_code, 200)
        self.assert_session_and_speaker_frames(resp.content)
        payload = form_payload(resp)
        payload["name"] = "DjangoCon"
        payload["with_billing"] = "on"
        payload["billing_company"] = "Acme Corp"
        payload["billing_vat_id"] = "DE123456789"
        payload["with_sessions"] = "on"
        payload[field_key(payload, "-title")] = "Opening Keynote"
        # the nested speakers formset of the one session row: fill its extra row, add a second one
        prefix = _speaker_prefix(payload)
        payload[f"{prefix}-0-name"] = "Ada Lovelace"
        payload[f"{prefix}-1-name"] = "Grace Hopper"
        payload[f"{prefix}-TOTAL_FORMS"] = "2"

        resp = self.client.post(reverse("conference-create"), payload)
        self.assertEqual(
            resp.status_code,
            302,
            getattr(resp, "context", None) and str(resp.context.get("form") and resp.context["form"].errors),
        )
        conference = Conference.objects.get(name="DjangoCon")
        self.assertEqual(conference.billing_company, "Acme Corp")
        self.assertEqual(Conference.objects.count(), 1)
        self.assertEqual(Session.objects.filter(conference=conference).count(), 1)
        self.assertEqual(
            sorted(Speaker.objects.filter(session__conference=conference).values_list("name", flat=True)),
            ["Ada Lovelace", "Grace Hopper"],
        )

    def test_billing_cleared_when_untoggled(self):
        conference = Conference.objects.create(
            name="Billed", with_billing=True, billing_company="Old Co", billing_vat_id="X1"
        )
        url = reverse("conference-update", kwargs={"pk": conference.pk})
        payload = form_payload(self.client.get(url))
        payload.pop("with_billing", None)
        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 302)
        conference.refresh_from_db()
        self.assertFalse(conference.with_billing)
        self.assertIn(conference.billing_company, (None, ""))
        self.assertIn(conference.billing_vat_id, (None, ""))

    def test_sessions_purged_with_nested_speakers(self):
        # plain POST, no JavaScript: untoggling with_sessions purges the sessions,
        # and their nested speakers go with them
        conference = Conference.objects.create(name="To Purge", with_sessions=True)
        session = Session.objects.create(conference=conference, title="Existing Session")
        Speaker.objects.create(session=session, name="Ada Lovelace")
        Speaker.objects.create(session=session, name="Grace Hopper")

        url = reverse("conference-update", kwargs={"pk": conference.pk})
        payload = form_payload(self.client.get(url))
        payload.pop("with_sessions", None)
        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 302)
        conference.refresh_from_db()
        self.assertFalse(conference.with_sessions)
        self.assertEqual(Session.objects.filter(conference=conference).count(), 0)
        self.assertEqual(Speaker.objects.filter(session__conference=conference).count(), 0)
        self.assertEqual(Speaker.objects.count(), 0)

    def test_detail_page_renders(self):
        conference = Conference.objects.create(name="Counted", with_sessions=True)
        Session.objects.create(conference=conference, title="Only Session")
        resp = self.client.get(reverse("conference-detail", kwargs={"pk": conference.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Counted")


class FormsetsConditionalCheckTest(TestCase):
    def test_no_check_errors(self):
        # the speakers formset is nested, so it carries no conditional (crud_views.E310)
        call_command("check")


class FormsetsConditionalSeedTest(TestCase):
    def test_seed_twice(self):
        call_command("seed")
        counts = (Conference.objects.count(), Session.objects.count(), Speaker.objects.count())
        call_command("seed")
        self.assertEqual((Conference.objects.count(), Session.objects.count(), Speaker.objects.count()), counts)
        self.assertEqual(Conference.objects.count(), 2)
        self.assertGreater(Speaker.objects.count(), 0)
