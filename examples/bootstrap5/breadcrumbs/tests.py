from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from breadcrumbs.models import Board, Workspace


class BreadcrumbsAppTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")
        cls.workspace = Workspace.objects.create(name="Acme")
        cls.board = Board.objects.create(title="Roadmap", workspace=cls.workspace)

    def setUp(self):
        self.client.force_login(self.admin)

    def test_list_shows_host_prefix(self):
        resp = self.client.get(reverse("workspace-list"))
        self.assertContains(resp, 'aria-label="breadcrumb"')
        self.assertContains(resp, "Host application")
        self.assertContains(resp, "Home")

    def test_board_detail_trail_contains_full_chain(self):
        resp = self.client.get(reverse("board-detail", kwargs={"workspace_pk": self.workspace.pk, "pk": self.board.pk}))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        nav = content.split('<nav aria-label="breadcrumb">')[1].split("</nav>")[0]
        pos = 0
        for expected in ["Home", "Host application", "Workspaces", "Acme", "Boards", "Roadmap"]:
            pos = nav.index(expected, pos)

    def test_last_item_is_active_not_a_link(self):
        resp = self.client.get(reverse("board-detail", kwargs={"workspace_pk": self.workspace.pk, "pk": self.board.pk}))
        self.assertContains(resp, 'aria-current="page"')
        content = resp.content.decode()
        active = content.split('aria-current="page"')[1].split("</li>")[0]
        self.assertNotIn("<a ", active)

    def test_host_page_renders(self):
        resp = self.client.get(reverse("breadcrumbs-host"))
        self.assertContains(resp, "Fake host application")
