from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from project.seeding import grant_model_perms

from context_buttons.models import Ticket


class ContextButtonsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.editor = User.objects.create_user(username="editor-test", password="pw")
        grant_model_perms(cls.editor, Ticket)
        cls.viewer = User.objects.create_user(username="viewer-test", password="pw")
        grant_model_perms(cls.viewer, Ticket, actions=("view",))
        cls.ticket = Ticket.objects.create(title="Printer on fire", priority=Ticket.Priority.HIGH)
        cls.update_url = reverse("ticket-update", kwargs={"pk": cls.ticket.pk})
        cls.delete_url = reverse("ticket-delete", kwargs={"pk": cls.ticket.pk})

    def detail(self, user):
        self.client.force_login(user)
        resp = self.client.get(reverse("ticket-detail", kwargs={"pk": self.ticket.pk}))
        self.assertEqual(resp.status_code, 200)
        return resp


class TicketDetailEditorTest(ContextButtonsTestCase):
    def test_header_uses_inline_template_code_button(self):
        self.assertContains(self.detail(self.editor), 'class="btn btn-primary btn-lg cv-demo-edit-big"')

    def test_manual_toolbar_renders_file_template_button(self):
        resp = self.detail(self.editor)
        self.assertContains(resp, 'id="manual-toolbar"')
        self.assertContains(resp, 'cv-demo-edit-pill"')

    def test_url_tile_links_to_update(self):
        resp = self.detail(self.editor)
        tile = f'href="{self.update_url}?cv_from=detail" class="card text-decoration-none" id="url-tile"'
        self.assertContains(resp, tile)

    def test_gated_section_shown(self):
        self.assertContains(self.detail(self.editor), 'id="gated-section"')

    def test_renders_german(self):
        self.client.force_login(self.editor)
        resp = self.client.get(reverse("ticket-detail", kwargs={"pk": self.ticket.pk}), HTTP_ACCEPT_LANGUAGE="de")
        self.assertContains(resp, "Gefahrenzone")
        self.assertContains(resp, "Dieses Ticket bearbeiten")

    def test_custom_loop_wraps_each_button(self):
        resp = self.detail(self.editor)
        # home, edit_big, delete + manage (appended by CRUD_VIEWS_MANAGE_VIEWS_ENABLED)
        self.assertContains(resp, 'class="cv-demo-loop-item"', count=4)


class TicketDetailViewerTest(ContextButtonsTestCase):
    def test_no_edit_or_delete_link_anywhere(self):
        resp = self.detail(self.viewer)
        self.assertNotContains(resp, self.update_url)
        self.assertNotContains(resp, self.delete_url)

    def test_no_custom_button_markup(self):
        resp = self.detail(self.viewer)
        # a raw closing quote: the code panel shows the same class names, but HTML-escaped (&quot;)
        self.assertNotContains(resp, 'cv-demo-edit-big"')
        self.assertNotContains(resp, 'cv-demo-edit-pill"')

    def test_url_tile_replaced_by_hint(self):
        resp = self.detail(self.viewer)
        self.assertNotContains(resp, 'id="url-tile"')
        self.assertContains(resp, 'id="url-tile-hidden"')

    def test_gated_section_absent(self):
        self.assertNotContains(self.detail(self.viewer), 'id="gated-section"')

    def test_custom_loop_only_lists_accessible_buttons(self):
        # home + manage; edit_big and delete are filtered out
        self.assertContains(self.detail(self.viewer), 'class="cv-demo-loop-item"', count=2)


class TicketCrudTest(ContextButtonsTestCase):
    def test_list_renders_with_snippets(self):
        self.client.force_login(self.viewer)
        resp = self.client.get(reverse("ticket-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Printer on fire")
        self.assertContains(resp, "snippet-panels")

    def test_template_shown_in_code_panel(self):
        resp = self.detail(self.viewer)
        self.assertContains(resp, "context_buttons/templates/context_buttons/ticket_detail.html")

    def test_viewer_cannot_open_update(self):
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(self.update_url).status_code, 403)

    def test_editor_updates_ticket(self):
        self.client.force_login(self.editor)
        resp = self.client.post(self.update_url, {"title": "Printer fixed", "priority": "low", "description": ""})
        self.assertEqual(resp.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.title, "Printer fixed")


class ContextButtonsSeedTest(TestCase):
    def test_seed_twice_and_bob_is_view_only(self):
        from django.core.management import call_command

        call_command("seed")
        count = Ticket.objects.count()
        call_command("seed")
        self.assertEqual(Ticket.objects.count(), count)
        self.assertGreater(count, 0)
        bob = get_user_model().objects.get(username="bob")
        alice = get_user_model().objects.get(username="alice")
        self.assertTrue(bob.has_perm("context_buttons.view_ticket"))
        self.assertFalse(bob.has_perm("context_buttons.change_ticket"))
        self.assertFalse(bob.has_perm("context_buttons.delete_ticket"))
        self.assertTrue(alice.has_perm("context_buttons.change_ticket"))
