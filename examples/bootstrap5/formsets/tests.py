import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from lxml import html
from project.testing import field_key, field_keys, form_payload

from formsets.models import Checklist, ChecklistItem, Choice, Question, Questionnaire


class ChecklistRegistrationTest(TestCase):
    def test_checklist_has_distinct_viewset(self):
        from formsets import views

        self.assertTrue(hasattr(views, "cv_checklist"), "A separate Checklist ViewSet must be registered")
        self.assertIsNot(views.cv_checklist, views.cv_questionnaire)
        for action in ("list", "create", "update"):
            self.assertIn(action, views.cv_checklist.get_all_views())
            kwargs = {"pk": 1} if action == "update" else None
            self.assertNotEqual(reverse(f"checklist-{action}", kwargs=kwargs), reverse("questionnaire-list"))


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


class ChecklistCrudTest(FormsetsTestCase):
    def assert_plain_items(self, content):
        document = html.fromstring(content)
        rows = document.cssselect(".cv-formset-row")
        self.assertTrue(rows)
        self.assertTrue(all("cv-formset-row-plain" in row.classes for row in rows))
        self.assertFalse(document.cssselect(".cv-formset-row-card, .cv-formset-row-legend"))

    def make_checklist(self):
        checklist = Checklist.objects.create(title="Release checklist")
        ChecklistItem.objects.create(checklist=checklist, label="Review changes", done=True)
        ChecklistItem.objects.create(checklist=checklist, label="Publish", done=False)
        return checklist

    def fragment_params(self, response):
        content = html.fromstring(response.content).cssselect(".cv-formset-content")[0]
        data = json.loads(content.get("cv-data-formset"))
        return {
            "template": "|".join(data["hierarchy"]),
            "pk": data["prefix_key"].rsplit("-", 2)[-2],
            "num": form_payload(response)[f"{content.get('cv-data-formset-prefix')}-TOTAL_FORMS"],
            "formset_parent_prefix_key": data["parent_prefix_key"],
        }

    def test_create_with_native_checked_and_omitted_values_and_fragment(self):
        url = reverse("checklist-create")
        response = self.client.get(url)
        self.assert_plain_items(response.content)
        payload = form_payload(response)
        payload["title"] = "New checklist"
        label = field_key(payload, "-label")
        payload[label] = "Checked item"
        payload[label.removesuffix("label") + "done"] = "on"
        fragment = self.client.get(url, self.fragment_params(response))
        self.assertEqual(fragment.status_code, 200)
        document = html.fromstring(fragment.json()["html"])
        self.assert_plain_items(fragment.json()["html"])
        for control in document.cssselect("input[name]"):
            if control.get("type") != "checkbox":
                payload[control.get("name")] = control.get("value", "")
        added_label = document.cssselect('input[name$="-label"]')[0].get("name")
        payload[added_label] = "Unchecked added item"
        total = field_key(payload, "-TOTAL_FORMS")
        payload[total] = str(int(payload[total]) + 1)
        ids = [el.get("id") for el in document.cssselect("[id]")]
        self.assertEqual(len(ids), len(set(ids)))
        for control in document.cssselect('input[name$="-label"], input[name$="-done"]'):
            self.assertEqual(len(document.xpath("//label[@for=$id]", id=control.get("id"))), 1)
            self.assertNotIn(control.get("name"), form_payload(response))
        saved = self.client.post(url, payload)
        self.assertRedirects(saved, reverse("checklist-list"))
        checklist = Checklist.objects.get(title=payload["title"])
        self.assertEqual(
            list(checklist.items.values_list("label", "done")),
            [("Checked item", True), ("Unchecked added item", False)],
        )

    def test_update_omitted_checkbox_saves_false_and_untouched_extra_stays_empty(self):
        checklist = self.make_checklist()
        url = reverse("checklist-update", kwargs={"pk": checklist.pk})
        initial = self.client.get(url)
        self.assert_plain_items(initial.content)
        payload = form_payload(initial)
        done_keys = [key for key in payload if key.endswith("-done")]
        self.assertEqual(len(done_keys), 1)
        payload.pop(done_keys[0])
        self.assertRedirects(self.client.post(url, payload), reverse("checklist-list"))
        self.assertEqual(list(checklist.items.values_list("done", flat=True)), [False, False])
        reloaded = form_payload(self.client.get(url))
        self.assertFalse(any(key.endswith("-done") for key in reloaded))
        self.assertEqual(checklist.items.count(), 2)

    def test_invalid_label_is_atomic_and_keeps_checked_state_then_corrects(self):
        checklist = self.make_checklist()
        url = reverse("checklist-update", kwargs={"pk": checklist.pk})
        payload = form_payload(self.client.get(url))
        label = next(key for key in field_keys(payload, "-label") if payload[key] == "Review changes")
        payload["title"] = "Edited title"
        payload[label] = "x" * 201
        response = self.client.post(url, payload)
        self.assertContains(response, "Ensure this value has at most 200 characters")
        self.assert_plain_items(response.content)
        self.assertEqual(form_payload(response)[label], "x" * 201)
        self.assertIn(label.removesuffix("label") + "done", form_payload(response))
        checklist.refresh_from_db()
        self.assertEqual(checklist.title, "Release checklist")
        self.assertEqual(
            list(checklist.items.values_list("label", "done")), [("Review changes", True), ("Publish", False)]
        )

        payload[label] = "Reviewed changes"
        self.assertRedirects(self.client.post(url, payload), reverse("checklist-list"))
        self.assertTrue(checklist.items.get(label="Reviewed changes").done)

    def test_hidden_delete_can_be_unmarked_before_deleting(self):
        checklist = self.make_checklist()
        url = reverse("checklist-update", kwargs={"pk": checklist.pk})
        response = self.client.get(url)
        document = html.fromstring(response.content)
        fields = document.cssselect(".cv-formset-compact-fields")
        self.assertTrue(fields)
        for grid in fields:
            self.assertFalse(grid.cssselect('input[type="hidden"]'))
        payload = form_payload(response)
        label = next(key for key in field_keys(payload, "-label") if payload[key] == "Review changes")
        delete_key = label.removesuffix("label") + "DELETE"
        payload[delete_key] = "on"
        payload[delete_key] = ""  # what the existing unmark action submits
        self.assertRedirects(self.client.post(url, payload), reverse("checklist-list"))
        self.assertEqual(checklist.items.count(), 2)
        payload = form_payload(self.client.get(url))
        payload[delete_key] = "on"
        self.assertRedirects(self.client.post(url, payload), reverse("checklist-list"))
        self.assertEqual(list(checklist.items.values_list("label", flat=True)), ["Publish"])

    def test_foreign_child_id_is_rejected_without_storage_changes(self):
        checklist = self.make_checklist()
        foreign_parent = Checklist.objects.create(title="Other owner")
        foreign = ChecklistItem.objects.create(checklist=foreign_parent, label="Foreign", done=True)
        url = reverse("checklist-update", kwargs={"pk": checklist.pk})
        payload = form_payload(self.client.get(url))
        id_key = field_keys(payload, "-id")[0]
        payload[id_key] = str(foreign.pk)
        payload["title"] = "Must not save"
        before = list(ChecklistItem.objects.values_list("pk", "checklist_id", "label", "done"))
        self.assertEqual(self.client.post(url, payload).status_code, 200)
        checklist.refresh_from_db()
        self.assertEqual(checklist.title, "Release checklist")
        self.assertEqual(list(ChecklistItem.objects.values_list("pk", "checklist_id", "label", "done")), before)

    def test_anonymous_and_no_permission_users_cannot_read_fragments_or_write(self):
        checklist = self.make_checklist()
        reader = get_user_model().objects.create_user(username="checklist-denied", password="pw")
        for action in ("list", "create", "update"):
            url = reverse(f"checklist-{action}", kwargs={"pk": checklist.pk} if action == "update" else None)
            self.client.force_login(self.admin)
            page = self.client.get(url)
            payload = form_payload(page) if action != "list" else {}
            params = self.fragment_params(page) if action != "list" else {}
            for user in (None, reader):
                with self.subTest(action=action, user=user):
                    self.client.logout()
                    if user:
                        self.client.force_login(user)
                    for response in (
                        self.client.get(url),
                        self.client.get(url, params),
                        self.client.post(url, payload),
                    ):
                        self.assertIn(response.status_code, (302, 403))
                        self.assertNotContains(response, "cv-formset-row-compact", status_code=response.status_code)
                    checklist.refresh_from_db()
                    self.assertEqual(checklist.title, "Release checklist")
                    self.assertEqual(Checklist.objects.count(), 1)
                    self.assertEqual(
                        list(checklist.items.values_list("label", "done")),
                        [("Review changes", True), ("Publish", False)],
                    )


class ChecklistDiscoveryTest(FormsetsTestCase):
    def test_landing_links_to_checklist_and_back(self):
        landing = self.client.get(reverse("questionnaire-list"))
        document = html.fromstring(landing.content)
        links = document.xpath("//a[@href=$url]", url=reverse("checklist-list"))
        self.assertTrue(any("Checklist example" in link.text_content() for link in links))
        page = self.client.get(reverse("checklist-list"))
        document = html.fromstring(page.content)
        links = document.xpath("//a[@href=$url]", url=reverse("questionnaire-list"))
        self.assertTrue(any("Questionnaire examples" in link.text_content() for link in links))

    def test_seed_is_idempotent_preserves_edits_and_demo_users_can_edit(self):
        from django.core.management import call_command

        call_command("seed")
        checklist = Checklist.objects.get(title="Release checklist")
        self.assertEqual(list(checklist.items.values_list("done", flat=True)), [True, False])
        item = checklist.items.first()
        item.done = False
        item.save()
        counts = (Checklist.objects.count(), ChecklistItem.objects.count())
        call_command("seed")
        self.assertEqual((Checklist.objects.count(), ChecklistItem.objects.count()), counts)
        item.refresh_from_db()
        self.assertFalse(item.done)
        for username in ("alice", "bob"):
            user = get_user_model().objects.get(username=username)
            self.assertFalse(user.is_superuser)
            self.client.force_login(user)
            create = reverse("checklist-create")
            page = self.client.get(create)
            self.assertEqual(page.status_code, 200)
            payload = form_payload(page)
            payload["title"] = f"{username} checklist"
            label = field_key(payload, "-label")
            payload[label] = "Demo task"
            payload[label.removesuffix("label") + "done"] = "on"
            self.assertRedirects(self.client.post(create, payload), reverse("checklist-list"))
            created = Checklist.objects.get(title=payload["title"])
            update = reverse("checklist-update", kwargs={"pk": created.pk})
            page = self.client.get(update)
            params = ChecklistCrudTest.fragment_params(self, page)
            self.assertEqual(self.client.get(update, params).status_code, 200)
            payload = form_payload(page)
            payload.pop(next(key for key in payload if key.endswith("-done")))
            self.assertRedirects(self.client.post(update, payload), reverse("checklist-list"))
            self.assertFalse(created.items.get().done)


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
