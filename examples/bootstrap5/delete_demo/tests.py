import re
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from guardian.models import UserObjectPermission
from lxml import html

from delete_demo.models import Milestone, Project, Task

MODAL = {"HTTP_X_CV_MODAL": "true"}


class DeleteDemoTestCase(TestCase):
    """Runs against the seeded data, logged in as alice."""

    def setUp(self):
        call_command("seed")
        self.alice = get_user_model().objects.get(username="alice")
        self.client.force_login(self.alice)

    @staticmethod
    def delete_url(title):
        return reverse("project-delete", kwargs={"pk": Project.objects.get(title=title).pk})


class BlockedCasesTest(DeleteDemoTestCase):
    def test_finite_and_unlimited_previews_keep_plain_blockers_and_rows(self):
        from delete_demo.views import ProjectDeleteView

        notice = "This preview is shortened. Additional objects are not shown."
        before = {model: set(model.objects.values_list("pk", flat=True)) for model in (Project, Task, Milestone)}
        for title in ("Website relaunch", "Office move"):
            visible = title == "Website relaunch"
            for limit in (1, None):
                for modal in (False, True):
                    for method in ("get", "post"):
                        with (
                            self.subTest(title=title, limit=limit, modal=modal, method=method),
                            patch.object(ProjectDeleteView, "cv_delete_preview_limit", limit),
                        ):
                            response = getattr(self.client, method)(
                                self.delete_url(title), {"confirm": True}, **(MODAL if modal else {})
                            )
                            self.assertEqual(response.status_code, 422 if modal and method == "post" else 200)
                            self.assertTrue(response.context["has_protected_objects"])
                            entries = response.context["protected_objects"]
                            self.assertEqual(len(entries), (1 if limit == 1 else 2) if visible else 0)
                            self.assertTrue(all(entry["url"] is None for entry in entries))
                            document = html.fromstring(response.content)
                            self.assertEqual(document.text_content().count(notice), int(visible and limit == 1))
                            self.assertFalse(document.xpath('//form[.//*[@name="confirm"]]'))
                            for task in Task.objects.filter(project__title=title):
                                self.assertFalse(
                                    document.xpath(
                                        "//a[@href=$url]", url=reverse("task-detail", kwargs={"pk": task.pk})
                                    )
                                )
                                if not visible:
                                    self.assertNotIn(task.title, document.text_content())
                            for model, pks in before.items():
                                self.assertEqual(set(model.objects.values_list("pk", flat=True)), pks)

    def test_demo_and_tutorials_teach_plain_blockers_and_cascade_links(self):
        docs = Path(__file__).resolve().parents[3] / "docs/getting_started"
        for name in ("demo.md", "tutorial-5-filters-permissions.md", "tutorial-6-books.md"):
            text = (docs / name).read_text()
            self.assertIn("plain text", text, name)
            self.assertIn("Book links", text, name)
            self.assertNotIn("linked Contract", text, name)
            self.assertNotIn("entry point is the protected link", text, name)
            self.assertNotIn("links to a full detail page, even from the modal", text, name)

    def test_case1_lists_own_blocking_tasks(self):
        resp = self.client.get(self.delete_url("Website relaunch"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Deletion is blocked by protected relationships:")
        self.assertContains(resp, "Draft the sitemap")
        self.assertContains(resp, "Pick a new theme")
        self.assertNotContains(resp, 'name="delete"')

    def test_case2_hides_bobs_task(self):
        resp = self.client.get(self.delete_url("Office move"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Other objects still reference this one")
        self.assertNotContains(resp, "Book the movers")
        bobs_task = Task.objects.get(title="Book the movers")
        self.assertNotContains(resp, reverse("task-detail", kwargs={"pk": bobs_task.pk}))
        self.assertNotContains(resp, 'name="delete"')

    def test_case3_business_rule(self):
        resp = self.client.get(self.delete_url("Annual report"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "A shared project cannot be deleted. Stop sharing it first.")
        self.assertNotContains(resp, 'name="delete"')

    def test_blocked_post_deletes_nothing(self):
        url = self.delete_url("Office move")
        resp = self.client.post(url, {"confirm": True})
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "Book the movers", status_code=200)
        resp = self.client.post(url, {"confirm": True}, **MODAL)
        self.assertEqual(resp.status_code, 422)
        self.assertNotContains(resp, "Book the movers", status_code=422)
        self.assertTrue(Project.objects.filter(title="Office move").exists())


class DeletableTest(DeleteDemoTestCase):
    def test_deletable_shows_cascade_preview(self):
        resp = self.client.get(self.delete_url("Old prototype"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "The following related objects will also be deleted:")
        self.assertContains(resp, "Clickable mockup")
        self.assertContains(resp, "User test round")
        self.assertContains(resp, 'name="delete"')

    def test_delete_cascades(self):
        url = self.delete_url("Old prototype")
        resp = self.client.post(url, {"confirm": True})
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Project.objects.filter(title="Old prototype").exists())
        self.assertFalse(Milestone.objects.filter(title="Clickable mockup").exists())

    def test_modal_delete(self):
        project = Project.objects.get(title="Old prototype")
        resp = self.client.get(reverse("project-detail", kwargs={"pk": project.pk}))
        self.assertEqual(resp.status_code, 200)
        delete_url = reverse("project-delete", kwargs={"pk": project.pk})
        # any <a> whose href points at the delete view and that carries data-cv-modal, in either attribute order
        tags = [tag for tag in re.findall(r"<a\b[^>]*>", resp.content.decode()) if "data-cv-modal" in tag]
        self.assertTrue(any(re.search(rf'href="{re.escape(delete_url)}[?"]', tag) for tag in tags), tags)
        # the modal partial itself
        resp = self.client.get(delete_url, **MODAL)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "data-cv-modal-dismiss")


class ProjectCreateTest(DeleteDemoTestCase):
    def test_create_assigns_creator_perms(self):
        resp = self.client.post(reverse("project-create"), {"title": "New idea"})
        self.assertEqual(resp.status_code, 302)
        project = Project.objects.get(title="New idea")
        self.assertEqual(project.owner, self.alice)
        for key in ("project-detail", "project-update", "project-delete"):
            self.assertEqual(self.client.get(reverse(key, kwargs={"pk": project.pk})).status_code, 200, key)


class VisibilityTest(DeleteDemoTestCase):
    def test_task_list_hides_bobs_task(self):
        resp = self.client.get(reverse("task-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Draft the sitemap")
        self.assertNotContains(resp, "Book the movers")

    def test_bob_sees_his_own_project(self):
        self.client.force_login(get_user_model().objects.get(username="bob"))
        resp = self.client.get(reverse("project-list"))
        self.assertContains(resp, "Garden shed")
        # the About panel names alice's projects, so check her rows' detail links instead
        office_move = Project.objects.get(title="Office move")
        self.assertNotContains(resp, reverse("project-detail", kwargs={"pk": office_move.pk}))


class SeedTest(TestCase):
    def test_seed_idempotent(self):
        def counts():
            return [m.objects.count() for m in (Project, Task, Milestone, UserObjectPermission)]

        call_command("seed")
        first = counts()
        call_command("seed")
        self.assertEqual(counts(), first)
