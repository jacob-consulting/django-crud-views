"""#179: backend-only views still render action labels when shown as buttons, so E110 checks them."""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorListView, cv_author


def e110_messages(view_cls) -> list:
    return [m.msg for c in view_cls.checks() for m in c.messages() if m.id == "viewset.E110"]


@pytest.mark.django_db
def test_backend_only_view_without_labels_reports_e110(cv_author_origin):
    from crud_views.lib.views import ActionView

    class NoLabelsView(ActionView):
        cv_viewset = cv_author_origin
        cv_key = "e110_no_labels"
        cv_path = "e110-no-labels"
        cv_backend_only = True

        def action(self, context):
            return True

    msgs = e110_messages(NoLabelsView)
    assert len(msgs) == 2
    assert any("»cv_action_label_template»" in m for m in msgs)
    assert any("»cv_action_short_label_template»" in m for m in msgs)


@pytest.mark.django_db
def test_backend_only_view_with_labels_needs_no_header_or_paragraph(cv_author_origin):
    from crud_views.lib.views import ActionView

    class LabelsOnlyView(ActionView):
        cv_viewset = cv_author_origin
        cv_key = "e110_labels_only"
        cv_path = "e110-labels-only"
        cv_backend_only = True
        cv_header_template = None
        cv_paragraph_template = None
        cv_action_label_template = None
        cv_action_short_label_template = None
        cv_action_label_template_code = "Go"
        cv_action_short_label_template_code = "Go"

        def action(self, context):
            return True

    assert e110_messages(LabelsOnlyView) == []


def test_test_app_ping_views_pass_e110():
    from tests.test1.app.views import AuthorHookPingView, AuthorMutedPingView, AuthorPingView, AuthorSilentPingView

    for view in (AuthorPingView, AuthorSilentPingView, AuthorMutedPingView, AuthorHookPingView):
        assert e110_messages(view) == [], view


@pytest.mark.django_db
def test_backend_only_list_action_renders(author_douglas_adams, monkeypatch):
    user = User.objects.create_user(username="ping_179", password="pw")
    for perm in ("view", "change"):
        user_viewset_permission(user, cv_author, perm)
    client = Client()
    client.force_login(user)
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "ping"])
    resp = client.get(reverse(cv_author.get_router_name("list")))
    assert resp.status_code == 200
    assert b'cv-key="ping"' in resp.content
