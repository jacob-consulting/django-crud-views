from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from formsets.models import Choice, Question, Questionnaire
from project.testing import field_key, field_keys, form_payload


class FormsetsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")

    def setUp(self):
        self.client.force_login(self.admin)


class QuestionnaireCrudTest(FormsetsTestCase):
    def test_list_renders_with_snippets(self):
        Questionnaire.objects.create(title="Customer Survey")
        resp = self.client.get(reverse("questionnaire-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Customer Survey")
        self.assertContains(resp, "snippet-panels")

    def test_create_with_inline_question(self):
        resp = self.client.get(reverse("questionnaire-create"))
        self.assertEqual(resp.status_code, 200)

        payload = form_payload(resp)
        payload["title"] = "Onboarding Feedback"
        # fill the one blank extra question row and its blank extra choice row
        payload[field_key(payload, "-text")] = "How was your first week?"
        payload[field_key(payload, "-label")] = "Great"

        resp = self.client.post(reverse("questionnaire-create"), payload)
        self.assertEqual(
            resp.status_code,
            302,
            getattr(resp, "context", None) and str(resp.context.get("form") and resp.context["form"].errors),
        )
        questionnaire = Questionnaire.objects.get(title="Onboarding Feedback")
        question = Question.objects.get(questionnaire=questionnaire, text="How was your first week?")
        self.assertTrue(Choice.objects.filter(question=question, label="Great").exists())

    def test_create_without_inline_rows(self):
        resp = self.client.get(reverse("questionnaire-create"))
        payload = form_payload(resp)
        payload["title"] = "Empty Survey"
        resp = self.client.post(reverse("questionnaire-create"), payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Questionnaire.objects.get(title="Empty Survey").questions.count(), 0)

    def test_update_changes_inline_question(self):
        questionnaire = Questionnaire.objects.create(title="Exit Survey")
        question = Question.objects.create(questionnaire=questionnaire, text="Why are you leaving?")

        url = reverse("questionnaire-update", kwargs={"pk": questionnaire.pk})
        resp = self.client.get(url)
        payload = form_payload(resp)

        key = next(k for k in field_keys(payload, "-text") if payload[k] == "Why are you leaving?")
        payload[key] = "What could we improve?"

        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 302)
        question.refresh_from_db()
        self.assertEqual(question.text, "What could we improve?")


class FormsetsSeedTest(TestCase):
    def test_seed_twice(self):
        from django.core.management import call_command

        call_command("seed")
        counts = (Questionnaire.objects.count(), Question.objects.count(), Choice.objects.count())
        call_command("seed")
        self.assertEqual((Questionnaire.objects.count(), Question.objects.count(), Choice.objects.count()), counts)
        self.assertGreater(Questionnaire.objects.count(), 0)
