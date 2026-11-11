import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from lxml import html
from project.testing import field_key, field_keys, form_payload

from formsets.models import Choice, Question, Questionnaire


class FormsetsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")

    def setUp(self):
        self.client.force_login(self.admin)


class QuestionnaireCrudTest(FormsetsTestCase):
    def test_classic_invalid_nested_choice_redisplays_without_saving(self):
        questionnaire = Questionnaire.objects.create(title="Classic invalid")
        question = Question.objects.create(questionnaire=questionnaire, text="Unchanged")
        choice = Choice.objects.create(question=question, label="Unchanged")
        url = reverse("questionnaire-update", kwargs={"pk": questionnaire.pk})
        payload = form_payload(self.client.get(url))
        key = next(key for key in field_keys(payload, "-label") if payload[key] == choice.label)
        payload[key] = "x" * 101
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ensure this value has at most 100 characters")
        self.assertEqual(form_payload(response)[key], "x" * 101)
        choice.refresh_from_db()
        self.assertEqual(choice.label, "Unchanged")

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


class CompactQuestionnaireTest(FormsetsTestCase):
    def compact_url(self, action, questionnaire=None):
        from formsets.views import cv_questionnaire

        self.assertIn(f"compact_{action}", cv_questionnaire.get_all_views())
        return reverse(f"questionnaire-compact_{action}", kwargs={"pk": questionnaire.pk} if questionnaire else None)

    def fragment_params(self, response, index=0):
        doc = html.fromstring(response.content)
        content = doc.cssselect(".cv-formset-content")[index]
        data = json.loads(content.get("cv-data-formset"))
        payload = form_payload(response)
        return {
            "template": "|".join(data["hierarchy"]),
            "pk": data["prefix_key"].rsplit("-", 2)[-2],
            "num": payload[f"{content.get('cv-data-formset-prefix')}-TOTAL_FORMS"],
            "formset_parent_prefix_key": data["parent_prefix_key"],
        }

    def test_compact_create_saves_nested_records_and_redirect(self):
        url = self.compact_url("create")
        response = self.client.get(url)
        self.assertContains(response, "cv-formset-row-compact")
        payload = form_payload(response)
        payload["title"] = "Compact survey"
        payload[field_key(payload, "-text")] = "First question"
        payload[field_key(payload, "-label")] = "First choice"
        saved = self.client.post(url, payload, follow=True)
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(len(saved.redirect_chain), 1)
        questionnaire = Questionnaire.objects.get(title="Compact survey")
        question = questionnaire.questions.get(text="First question")
        self.assertEqual(list(question.choices.values_list("label", flat=True)), ["First choice"])

    def test_compact_update_and_invalid_nested_redisplay(self):
        questionnaire = Questionnaire.objects.create(title="Existing survey")
        question = Question.objects.create(questionnaire=questionnaire, text="Original question")
        choice = Choice.objects.create(question=question, label="Original choice")
        url = self.compact_url("update", questionnaire)
        payload = form_payload(self.client.get(url))
        text_key = next(key for key in field_keys(payload, "-text") if payload[key] == question.text)
        label_key = next(key for key in field_keys(payload, "-label") if payload[key] == choice.label)
        payload[text_key] = "Edited question"
        payload[label_key] = "x" * 101
        invalid = self.client.post(url, payload)
        self.assertEqual(invalid.status_code, 200)
        self.assertContains(invalid, "cv-formset-row-compact")
        self.assertContains(invalid, "Ensure this value has at most 100 characters")
        self.assertEqual(form_payload(invalid)[label_key], "x" * 101)
        choice.refresh_from_db()
        self.assertEqual(choice.label, "Original choice")
        payload[label_key] = "Edited choice"
        extra_text = next(key for key in field_keys(payload, "-text") if not payload[key])
        payload[extra_text] = "Added question"
        extra_label = field_keys(payload, "-label")[-1]  # the last extra question owns this choice
        payload[extra_label] = "Added nested choice"
        saved = self.client.post(url, payload, follow=True)
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(len(saved.redirect_chain), 1)
        question.refresh_from_db()
        choice.refresh_from_db()
        self.assertEqual(question.text, "Edited question")
        self.assertEqual(choice.label, "Edited choice")
        self.assertEqual(choice.question_id, question.pk)
        added = questionnaire.questions.get(text="Added question")
        self.assertTrue(added.choices.filter(label="Added nested choice").exists())
        classic = self.client.get(reverse("questionnaire-update", kwargs={"pk": questionnaire.pk}))
        self.assertContains(classic, "Edited choice")
        self.assertContains(classic, "Added nested choice")
        self.assertNotContains(classic, 'class="cv-formset-row cv-formset-row-compact"')

    def test_classic_and_compact_comparison_links(self):
        questionnaire = Questionnaire.objects.create(title="Compare")
        for action in ("create", "update"):
            compact_url = self.compact_url(action, questionnaire if action == "update" else None)
            classic_url = reverse(
                f"questionnaire-{action}", kwargs={"pk": questionnaire.pk} if action == "update" else None
            )
            classic = self.client.get(classic_url)
            compact = self.client.get(compact_url)
            self.assertContains(classic, compact_url)
            self.assertContains(compact, classic_url)
            self.assertNotContains(classic, 'class="cv-formset-row cv-formset-row-compact"')
            self.assertContains(compact, 'class="cv-formset-row cv-formset-row-compact"')
        listing = self.client.get(reverse("questionnaire-list"))
        for label in ("Create classic", "Create compact", "Edit classic", "Edit compact"):
            self.assertContains(listing, label)
        document = html.fromstring(listing.content)
        for key in ("update", "compact_update"):
            link = document.cssselect(f'tbody a[cv-key="{key}"]')[0]
            self.assertFalse(link.cssselect(".visually-hidden"))
        for key in ("create", "compact_create"):
            self.assertTrue(document.cssselect(f'.dropdown-menu a[cv-key="{key}"]'))

    def test_fragments_keep_nonfirst_question_ownership(self):
        questionnaire = Questionnaire.objects.create(title="Fragments")
        first = Question.objects.create(questionnaire=questionnaire, text="First")
        second = Question.objects.create(questionnaire=questionnaire, text="Second")
        url = self.compact_url("update", questionnaire)
        response = self.client.get(url)
        for index in (0, 2):  # root questions, then choices belonging to the second question
            params = self.fragment_params(response, index)
            fragment = self.client.get(url, params)
            self.assertEqual(fragment.status_code, 200)
            doc = html.fromstring(fragment.json()["html"])
            rows = doc.cssselect(".cv-formset-row-compact")
            self.assertTrue(rows)
            if index == 2:
                self.assertEqual(params["pk"], str(second.pk))
                self.assertNotEqual(params["pk"], str(first.pk))
                prefix = rows[0].get("cv-data-formset-form-prefix")
                self.assertEqual(
                    prefix,
                    f"questions-choices-{params['formset_parent_prefix_key']}-{second.pk}-0-{params['num']}",
                )
                self.assertEqual(doc.cssselect('input[name$="-question"]')[0].get("name"), f"{prefix}-question")
                foreign = Questionnaire.objects.create(title="Other survey")
                foreign_question = Question.objects.create(questionnaire=foreign, text="Other owner")
                self.assertEqual(self.client.get(url, {**params, "pk": foreign_question.pk}).status_code, 400)

    def test_denied_pages_fragments_and_posts_leave_records_unchanged(self):
        questionnaire = Questionnaire.objects.create(title="Protected")
        question = Question.objects.create(questionnaire=questionnaire, text="Protected question")
        Choice.objects.create(question=question, label="Protected choice")
        reader = get_user_model().objects.create_user(username="reader", password="pw")
        reader.user_permissions.add(
            Permission.objects.get(content_type__app_label="formsets", codename="view_questionnaire")
        )
        for action in ("create", "update"):
            url = self.compact_url(action, questionnaire if action == "update" else None)
            self.client.force_login(self.admin)
            response = self.client.get(url)
            payload = form_payload(response)
            payload["title"] = "Unauthorized change"
            fragment = self.fragment_params(response)
            before = (Questionnaire.objects.count(), Question.objects.count(), Choice.objects.count())
            for user in (None, reader):
                with self.subTest(action=action, user=user):
                    self.client.logout()
                    if user:
                        self.client.force_login(user)
                    for result in (
                        self.client.get(url),
                        self.client.get(url, fragment),
                        self.client.post(url, payload),
                    ):
                        self.assertIn(result.status_code, (302, 403))
                        self.assertNotContains(result, "cv-formset-row-compact", status_code=result.status_code)
                    self.assertEqual(
                        (Questionnaire.objects.count(), Question.objects.count(), Choice.objects.count()), before
                    )
                    questionnaire.refresh_from_db()
                    self.assertEqual(questionnaire.title, "Protected")
                    self.assertEqual(Question.objects.get(pk=question.pk).text, "Protected question")
                    self.assertEqual(Choice.objects.get(question=question).label, "Protected choice")

    def test_seeded_users_can_create_and_edit_compact(self):
        from django.core.management import call_command

        call_command("seed")
        for username in ("alice", "bob"):
            user = get_user_model().objects.get(username=username)
            self.assertFalse(user.is_superuser)
            self.client.force_login(user)
            create_url = self.compact_url("create")
            response = self.client.get(create_url)
            self.assertEqual(response.status_code, 200)
            payload = form_payload(response)
            payload["title"] = f"{username} compact"
            payload[field_key(payload, "-text")] = "User question"
            payload[field_key(payload, "-label")] = "User choice"
            saved = self.client.post(create_url, payload, follow=True)
            self.assertEqual(saved.status_code, 200)
            questionnaire = Questionnaire.objects.get(title=payload["title"])
            update_url = self.compact_url("update", questionnaire)
            response = self.client.get(update_url)
            self.assertEqual(self.client.get(update_url, self.fragment_params(response)).status_code, 200)
            payload = form_payload(response)
            payload["title"] += " edited"
            saved = self.client.post(update_url, payload, follow=True)
            self.assertEqual(saved.status_code, 200)
            questionnaire.refresh_from_db()
            self.assertEqual(questionnaire.title, payload["title"])
