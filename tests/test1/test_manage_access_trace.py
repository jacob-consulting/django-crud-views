"""Opt-in diagnostics preserve the hosting viewer and use a separate trace actor."""

import json
from pathlib import Path

import pytest
from django.contrib.auth.models import Group
from django.template.loader import render_to_string
from django.test import override_settings
from django.urls import reverse
from lxml import html

from crud_views.lib.access_trace import AccessStep, AccessTrace
from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from crud_views.lib.views.manage import ManageView

pytestmark = pytest.mark.django_db


@pytest.fixture
def developer(django_user_model):
    user = django_user_model.objects.create_user(username="diagnostic developer")
    user.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    return user


@pytest.fixture(params=["cv_author", "cv_guardian_author"])
def host(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setitem(crud_views_settings.__dict__, "manage_access_trace", True)


def submit(client, host, user, **params):
    client.force_login(user)
    return client.get(reverse(host.get_router_name("manage")), params)


def test_setting_and_disabled_no_work(client, host, developer, monkeypatch):
    assert "manage_access_trace" in CrudViewsSettings.model_fields
    assert CrudViewsSettings.model_fields["manage_access_trace"].default is False

    def forbidden(*args, **kwargs):
        raise AssertionError("Disabled tracing must not interpret or resolve query inputs")

    monkeypatch.setattr(ManageView, "get_manage_access_trace", forbidden, raising=False)
    monkeypatch.setattr("crud_views.lib.views.manage.resolve_trace_user", forbidden, raising=False)
    response = submit(client, host, developer, cv_access_mode="path", cv_access_user="<bad>", cv_access_path="//bad")
    assert response.status_code == 200
    assert response.context["manage_access_trace"] is None
    assert not html.fromstring(response.content).cssselect("#cv-manage-access-trace")


def test_path_runs_under_actor_not_viewer(client, host, developer, django_user_model, enabled):
    actor = django_user_model.objects.create_user(username="<script>actor</script>")
    response = submit(
        client, host, developer, cv_access_mode="path", cv_access_user=actor.username, cv_access_path="/author/manage/"
    )
    assert response.status_code == 200
    result = response.context["manage_access_trace"]
    assert result["trace"]["outcome"] == "denied"
    assert result["actor"]["pk"] == str(actor.pk)
    assert result["trace"]["user"]["pk"] == str(actor.pk)
    assert response.wsgi_request.user.pk == developer.pk
    assert response.context["manage_permissions"]["actor"]["id"] == developer.pk
    assert int(client.session["_auth_user_id"]) == developer.pk
    assert "<script>actor</script>" not in response.content.decode()
    assert "&lt;script&gt;actor&lt;/script&gt;" in response.content.decode()
    card = html.fromstring(response.content).cssselect("#cv-manage-access-trace")[0]
    assert "denied" in card.text_content().lower()
    assert "other middleware and URL decorators are not traced" in card.text_content()


@pytest.mark.parametrize(
    "params",
    [
        {"cv_access_mode": "path", "cv_access_user": "<script>unknown</script>", "cv_access_path": "/author/"},
        {"cv_access_mode": "path", "cv_access_user": "", "cv_access_path": "/author/"},
        {"cv_access_mode": "bad", "cv_access_user": "diagnostic developer"},
        {"cv_access_mode": "path", "cv_access_user": "diagnostic developer", "cv_access_path": ""},
    ],
)
def test_invalid_query_feedback_without_trace(client, host, developer, enabled, monkeypatch, params):
    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid form must not trace")

    monkeypatch.setattr("crud_views.lib.views.manage.trace_access", forbidden, raising=False)
    response = submit(client, host, developer, **params)
    result = response.context["manage_access_trace"]
    assert result["error"] and result["trace"] is None and result["rows"] == []
    assert response.context["manage_permissions"]["actor"]["id"] == developer.pk
    assert "<script>unknown</script>" not in response.content.decode()


def test_host_gate_cannot_be_bypassed(client, host, developer, django_user_model, enabled, monkeypatch):
    outsider = django_user_model.objects.create_user(username="outside", is_superuser=True, is_staff=True)

    def forbidden(*args, **kwargs):
        raise AssertionError("Host gate must run before diagnostic input")

    monkeypatch.setattr("crud_views.lib.views.manage.resolve_trace_user", forbidden, raising=False)
    assert (
        submit(
            client,
            host,
            outsider,
            cv_access_mode="path",
            cv_access_user=developer.username,
            cv_access_path="/author/manage/",
        ).status_code
        == 403
    )


def test_explicit_builder_has_no_request_dependency(host, developer, monkeypatch):
    assert callable(getattr(ManageView, "get_manage_access_trace", None))

    def forbidden(self):
        raise AssertionError("Explicit builder must not read request")

    monkeypatch.setattr(ManageView, "request", property(forbidden), raising=False)
    result = host.get_view_class("manage")().get_manage_access_trace(host, developer, mode="path", path="/missing/")
    assert result["trace"]["outcome"] == "no_such_route"


def test_scalar_trace_errors_are_escaped(client, host, developer, enabled, monkeypatch):
    payload = "<script>alert('private')</script>"
    trace = AccessTrace(
        path=payload,
        view=payload,
        route=payload,
        outcome="error",
        decided_by=1,
        steps=[AccessStep(1, "custom_gate", result="error", exception={"class": "ValueError", "message": payload})],
    )
    monkeypatch.setattr("crud_views.lib.views.manage.trace_access", lambda *args: trace, raising=False)
    response = submit(
        client, host, developer, cv_access_mode="path", cv_access_user=developer.username, cv_access_path="/anything/"
    )
    assert payload not in response.content.decode()
    assert "&lt;script&gt;" in response.content.decode()
    assert "ValueError" in response.content.decode()
    assert "traceback" not in json.dumps(response.context["manage_access_trace"])


@pytest.mark.parametrize("kind", ["core", "guardian"])
def test_target_ancestor_is_actor_gate_but_host_ancestor_is_viewer_gate(
    client, developer, django_user_model, enabled, kind
):
    from crud_views.lib.views import DetailViewPermissionRequired
    from crud_views.lib.viewset import ParentViewSet, ViewSet
    from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Book, Publisher
    from tests.test1.test_ancestor_authorization import _url, isolated_routes
    from tests.test1.test_manage_requirements import grant, register

    def build(sfx):
        parent = ViewSet(model=Publisher, name="traceparent" + sfx)
        cls = GuardianViewSet if kind == "guardian" else ViewSet
        child = cls(model=Book, name="tracechild" + sfx, parent=ParentViewSet(name=parent.name, attribute="publisher"))
        register(GuardianDetailViewPermissionRequired if kind == "guardian" else DetailViewPermissionRequired, child)
        return (parent, child), [parent, child]

    with isolated_routes(build) as (parent, child):
        publisher = Publisher.objects.create(name="secret parent")
        obj = Book.objects.create(title="secret book", publisher=publisher)
        actor = django_user_model.objects.create_user(username="business actor", is_superuser=True)
        target = _url(child, "tested", **{child.parent.get_pk_name(): publisher.pk, child.pk_name: obj.pk})
        client.force_login(developer)
        response = client.get(
            "/author/manage/", {"cv_access_mode": "path", "cv_access_user": actor.username, "cv_access_path": target}
        )
        assert response.status_code == 200
        assert response.context["manage_access_trace"]["trace"]["outcome"] == "allowed"
        card = html.fromstring(response.content).cssselect("#cv-manage-access-trace")[0].text_content()
        assert "secret book" not in card and "secret parent" not in card
        hosting = _url(child, "manage", **{child.parent.get_pk_name(): publisher.pk})
        params = {"cv_access_mode": "path", "cv_access_user": actor.username, "cv_access_path": target}
        assert client.get(hosting, params).status_code == 403
        grant(developer, parent, "view")
        assert client.get(hosting, params).status_code == 200
        developer.groups.clear()
        assert client.get(hosting, params).status_code == 403


@pytest.mark.parametrize("mode", ["path", "viewset"])
@pytest.mark.parametrize("selector", ["username", "pk", "collision", "unknown", "invalid_pk"])
def test_both_forms_share_username_first_selection(client, host, developer, django_user_model, enabled, mode, selector):
    actor = django_user_model.objects.create_user(username="nonnumeric actor")
    identifier = actor.username
    if selector in {"pk", "collision"}:
        identifier = str(actor.pk)
    if selector == "collision":
        actor = django_user_model.objects.create_user(username=identifier)
    elif selector == "unknown":
        identifier = "987654321"
    elif selector == "invalid_pk":
        identifier = "not-a-valid-pk"
    response = submit(
        client, host, developer, cv_access_mode=mode, cv_access_user=identifier, cv_access_path="/author/manage/"
    )
    data = response.context["manage_access_trace"]
    assert data["user_input"] == identifier
    if selector in {"unknown", "invalid_pk"}:
        assert data["error"] and data["actor"] is None and not data["rows"] and data["trace"] is None
    else:
        assert data["actor"]["pk"] == str(actor.pk) and not data["error"]
        if mode == "viewset":
            assert response.context["manage_permissions"]["actor"]["id"] == actor.pk
            assert [row["key"] for row in data["rows"]] == list(host.get_all_views())
        else:
            assert data["trace"]["user"]["pk"] == str(actor.pk)


@pytest.mark.parametrize("empty_matrix", [False, True])
@pytest.mark.parametrize("state", ["other", "self", "disabled", "empty", "invalid", "unknown", "path"])
def test_only_successful_viewset_selection_changes_actor_label(
    client, host, developer, django_user_model, enabled, monkeypatch, empty_matrix, state
):
    from crud_views.lib.viewset import ViewSet

    actor = django_user_model.objects.create_user(username="selected actor")
    if empty_matrix:
        monkeypatch.setattr(ViewSet, "permissions", property(lambda self: {}))
    before = submit(client, host, developer).context["manage_permissions"]
    selected = actor if state == "other" else developer
    params = {"cv_access_mode": "viewset", "cv_access_user": selected.username}
    if state == "disabled":
        monkeypatch.setitem(crud_views_settings.__dict__, "manage_access_trace", False)
    elif state == "empty":
        params = {}
    elif state == "invalid":
        params["cv_access_mode"] = "invalid"
    elif state == "unknown":
        params["cv_access_user"] = "missing actor"
    elif state == "path":
        params.update(cv_access_mode="path", cv_access_path="/author/manage/")
    response = submit(client, host, developer, **params)
    checked = state in {"self", "other"}
    matrix = response.context["manage_permissions"]
    assert matrix["actor"]["id"] == (selected.pk if checked else developer.pk)
    assert {k: v for k, v in matrix.items() if k != "actor"} == {k: v for k, v in before.items() if k != "actor"}
    label = html.fromstring(response.content).cssselect("[data-manage-actor]")[0].text_content()
    assert ("(checked below)" in label) is checked
    assert ("(you)" in label) is not checked
    assert response.wsgi_request.user.pk == developer.pk


@pytest.mark.parametrize("object_pk", [None, "valid", "invalid"])
def test_route_inventory_and_own_pk_boundaries(host, developer, object_pk):
    obj = host.model.objects.create(first_name="not", last_name="rendered")
    pk = str(obj.pk) if object_pk == "valid" else "not-a-pk" if object_pk else None
    data = host.get_view_class("manage")().get_manage_access_trace(host, developer, mode="viewset", object_pk=pk)
    assert [r["key"] for r in data["rows"]] == list(host.get_all_views())
    rows = {row["key"]: row for row in data["rows"]}
    for key in ("detail", "update", "delete"):
        row = rows[key]
        if object_pk is None:
            assert row["instruction"] == "needs an object pk" and row["trace"] is None
        elif object_pk == "invalid":
            assert row["instruction"] == "use the path field" and row["trace"] is None
        else:
            assert row["path"] == reverse(host.get_router_name(key), kwargs={host.pk_name: pk})
            assert row["trace"] and not row["instruction"]
    for key in ("list", "create", "manage"):
        assert rows[key]["path"] == reverse(host.get_router_name(key))
        assert rows[key]["trace"] and not rows[key]["instruction"]


def test_nested_parent_coordinates_and_extra_routes(client, developer, enabled):
    from crud_views.lib.views import CreateView, DetailView, ListView
    from crud_views.lib.views.child import RedirectChildView
    from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
    from crud_views_polymorphic.lib.create import PolymorphicCreateView
    from tests.test1.app.models import Book, BookNote, Publisher
    from tests.test1.test_ancestor_authorization import _url, isolated_routes
    from tests.test1.test_manage_requirements import register

    def build(sfx):
        grand = ViewSet(model=Publisher, name="acgrand" + sfx, ancestor_policy=AncestorPolicy(provider="none"))
        parent = ViewSet(
            model=Book,
            name="acparent" + sfx,
            ancestor_policy=AncestorPolicy(provider="none"),
            parent=ParentViewSet(name=grand.name, attribute="publisher"),
        )
        leaf = ViewSet(
            model=BookNote,
            name="acleaf" + sfx,
            pk_name="note_id",
            parent=ParentViewSet(name=parent.name, attribute="book"),
        )
        for base, key in [
            (ListView, "list"),
            (CreateView, "create"),
            (DetailView, "detail"),
            (RedirectChildView, "redirect_child"),
            (PolymorphicCreateView, "polymorphic"),
        ]:
            register(base, leaf, key=key)
        register(CreateView, leaf, key="post_only", http_method_names=["post"], cv_backend_only=True)
        register(CreateView, leaf, key="custom", cv_path_contribute=classmethod(lambda cls: "(?P<extra>[a-z]+)/"))
        return (grand, parent, leaf), [grand, parent, leaf]

    with isolated_routes(build) as (_grand, parent, leaf):
        pub = Publisher.objects.create(name="hidden publisher")
        book = Book.objects.create(title="hidden book", publisher=pub)
        note = BookNote.objects.create(note="hidden note", book=book)
        coords = {parent.parent.get_pk_name(): pub.pk, leaf.parent.get_pk_name(): book.pk}
        client.force_login(developer)
        response = client.get(
            _url(leaf, "manage", **coords),
            {
                "cv_access_mode": "viewset",
                "cv_access_user": developer.username,
                "cv_access_pk": note.pk,
                **dict.fromkeys(coords, "987654"),
                "extra": "tampered",
                "polymorphic_ctype_id": "1",
                "redirect": "bad",
                "redirect_key": "bad",
            },
        )
        assert response.status_code == 200
        data = response.context["manage_access_trace"]
        assert [r["key"] for r in data["rows"]] == list(leaf.get_all_views())
        rows = {r["key"]: r for r in data["rows"]}
        assert rows["detail"]["path"] == _url(leaf, "detail", **coords, note_id=note.pk)
        assert rows["list"]["path"] == _url(leaf, "list", **coords)
        for key in ("redirect_child", "polymorphic", "custom"):
            assert rows[key]["instruction"] == "use the path field" and rows[key]["trace"] is None
        assert rows["post_only"]["trace"]
        assert any(step["result"] == "not_evaluated" for step in rows["post_only"]["trace"]["steps"])
        assert (
            "hidden note"
            not in html.fromstring(response.content).cssselect("#cv-manage-access-trace")[0].text_content()
        )


def test_selected_guardian_row_reuses_strict_counts_once(
    client, cv_guardian_author, developer, django_user_model, enabled, monkeypatch
):
    from guardian.shortcuts import assign_perm

    from crud_views_guardian.lib.views import GuardianManageView
    from tests.test1.test_manage_requirements import grant

    actor = django_user_model.objects.create_user(username="strict actor")
    obj = cv_guardian_author.model.objects.create(first_name="hidden", last_name="title")
    cv_guardian_author.model.objects.create(first_name="other", last_name="hidden")
    grant(actor, cv_guardian_author, "view")
    assign_perm(cv_guardian_author.permissions["view"], actor, obj)
    original = GuardianManageView.get_manage_actor_row
    calls = []

    def record(self, viewset, user):
        calls.append(user.pk)
        return original(self, viewset, user)

    monkeypatch.setattr(GuardianManageView, "get_manage_actor_row", record)
    response = submit(client, cv_guardian_author, developer, cv_access_mode="viewset", cv_access_user=actor.username)
    assert calls == [developer.pk, actor.pk]
    cell = next(c for c in response.context["manage_permissions"]["actor"]["cells"] if c["key"] == "view")
    assert cell["model"] is True and cell["object_count"] == 1


TRACE_CLASSES = {
    "allowed": "badge bg-success",
    "passed": "badge bg-success",
    "denied": "badge bg-danger",
    "not_found": "badge bg-warning text-dark",
    "login_redirect": "badge bg-warning text-dark",
    "error": "badge bg-warning text-dark",
    "no_such_route": "badge bg-warning text-dark",
    "not_evaluated": "badge bg-warning text-dark",
    "skipped": "badge bg-secondary",
    "not_reached": "badge bg-secondary",
}


@pytest.mark.parametrize("result", list(TRACE_CLASSES))
def test_every_result_uses_registry_and_semantic_wording(result):
    from crud_views.lib.button_classes import DEFAULT_BUTTON_CLASSES

    key = "manage:trace-" + result.replace("_", "-")
    assert DEFAULT_BUTTON_CLASSES.get(key) == TRACE_CLASSES[result]
    trace = AccessTrace(
        path="/example/", outcome=result, steps=[AccessStep(1, "own_permission", result=result)]
    ).to_dict()
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: "project-trace-status"}):
        doc = html.fromstring(render_to_string("crud_views/includes/access_trace.html", {"trace": trace}))
    badges = doc.cssselect("[data-cv-trace-result]")
    assert len(badges) == 2
    assert all(badge.get("class") == "project-trace-status" for badge in badges)
    assert all(badge.text_content().strip().lower() == result.replace("_", " ") for badge in badges)


def test_enabled_card_form_help_disclosure_and_csp_contract(client, host, developer, enabled, monkeypatch):
    monkeypatch.setattr(host.get_view_class("manage"), "manage_docs_base_url", "https://docs.example/manage/")
    with override_settings(
        CRUD_VIEWS_BUTTON_CLASSES={
            "manage:trace-allowed": "project-allowed",
            "form:submit": "project-submit",
            "manage:help": "project-help",
        }
    ):
        response = submit(client, host, developer, cv_access_mode="viewset", cv_access_user=developer.username)
    doc = html.fromstring(response.content)
    card = doc.cssselect("#cv-manage-access-trace")[0]
    assert card.getprevious().get("id") == "cv-manage-permissions"
    assert card.getnext().get("id") == "cv-manage-views"
    forms = card.cssselect("form")
    assert len(forms) == 2 and all(form.get("method").lower() == "get" for form in forms)
    assert [form.cssselect('input[name="cv_access_mode"]')[0].get("value") for form in forms] == ["viewset", "path"]
    assert all(form.cssselect('input[name="cv_access_user"][required]') for form in forms)
    assert all(form.cssselect('button[type="submit"].project-submit') for form in forms)
    assert not card.cssselect("select, datalist, input[type=checkbox], input[type=radio]")
    inputs = card.cssselect("input:not([type=hidden])")
    ids = [node.get("id") for node in inputs]
    assert len(ids) == len(set(ids)) and all(ids)
    assert all(len(card.cssselect(f'label[for="{identity}"]')) == 1 for identity in ids)
    assert len(doc.cssselect("[id]")) == len({el.get("id") for el in doc.cssselect("[id]")})
    link = card.cssselect("a[data-cv-manage-help]")[0]
    assert link.get("href") == "https://docs.example/manage/#access-check"
    assert link.get("target") == "_blank" and link.get("rel") == "noopener"
    assert link.get("aria-label") == "Documentation: Access check" and "new tab" in link.get("title")
    assert link.get("class") == "project-help" and link.text_content().strip() == "?"
    assert card.cssselect("details > summary") and not card.cssselect(
        "details[open], summary a, summary input, summary button"
    )
    assert card.cssselect("summary .project-allowed")
    for node in doc.iter():
        assert not any(name.lower().startswith("on") or name.lower() == "style" for name in node.attrib)
        if node.tag == "script":
            assert node.get("src") and not (node.text or "").strip()
    for region in doc.cssselect(".table-responsive"):
        assert region.get("role") == "region" and region.get("tabindex") == "0" and region.get("aria-label")
    assert all(th.get("scope") for th in doc.cssselect("th"))
    css = Path("src/crud_views/static/crud_views/css/manage.css").read_text()
    assert "[data-cv-manage] #cv-manage-access-trace" in css and "overflow-wrap: anywhere" in css


def test_partial_renders_provenance_counts_and_zero_counts():
    trace = AccessTrace(
        path="/path/",
        decided_by=3,
        plan=[{"kind": "ancestor_gate", "source": "ancestor_policy.read", "permission": "app.view_book"}],
        steps=[
            AccessStep(1, "list_filter", result="passed", counts={"visible": 0, "total": 5}),
            AccessStep(2, "list_filter", result="passed", counts={"visible": 0, "total": None}),
            AccessStep(
                3,
                "own_permission",
                result="denied",
                provider="model",
                how="no_permission",
                object={"model": "app.book", "pk": "2"},
            ),
        ],
    ).to_dict()
    text = html.fromstring(render_to_string("crud_views/includes/access_trace.html", {"trace": trace})).text_content()
    for expected in [
        "ancestor_policy.read",
        "app.view_book",
        "sees 0 of 5 objects",
        "0 rows",
        "model",
        "app.book",
        "decided at step 3",
    ]:
        assert expected in text
