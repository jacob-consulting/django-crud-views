"""Phase 6.2 D-12/D-13/D-14 (AUTH-07): native template overrides receive only safe, already-resolved context.

Six package templates are replaced through a locmem loader placed before the filesystem and app loaders
(``APP_DIRS=False``): the list content, the card, the action button leaf, the Guardian manage page, the alert frame
and the formset frame. The overrides use native ``dl``/``details``/``form``/``alert`` structures and only consume
the context the library already resolved (``object_list``, the card action group, the button leaf data, the
per-view ``guardian_policy``, the alert data, the formset data). They contain no permission logic, so whatever they
show is exactly what the library let through.

Allowed and denied requests come from the actor matrix in ``test_authorization_matrix.py``. Each case asserts the
allowed sentinel, the absence of forbidden rows/labels in both the HTML and the response context, and that
application-owned choices, structural formset hooks and literal escaping are preserved. This is post-fix
preservation evidence (A03); the defects were reproduced red in 06.2-01 (protected labels), 06.2-02 (child-page
create state, inactive rows) and 06.2-03 (fragment choices).

Routes are built by a yielding fixture on fresh, uniquely named ViewSets with a temporary ROOT_URLCONF; registry,
vocabulary and URL caches are restored in ``finally``. ``TEMPLATES`` is changed through pytest-django's ``settings``
fixture, whose teardown restores it and resets the template engines after every case (A08). The manage cases patch
the cached settings singleton with ``monkeypatch`` (A20).
"""

import copy
import re
import sys
import types
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.db.models import QuerySet
from django.template import Context, Template
from django.test import override_settings
from django.urls import clear_url_caches, include, path, reverse

from tests.test1.test_fragment_authorization import CHOICES, SECRET, PublisherMainForm, publisher_formsets

ALLOW_INACTIVE = "django.contrib.auth.backends.AllowAllUsersModelBackend"
INACTIVE_BACKENDS = [ALLOW_INACTIVE, "guardian.backends.ObjectPermissionBackend"]
LOGIN = "/accounts/login/"
MANAGE_GROUP = "mxt_manage_admins"
BLOCKED_HEADING = "Deletion is blocked by protected relationships"
BLOCKED_LIST_HEADING = BLOCKED_HEADING + ":"
BLOCKED_SENTENCE = "Other objects still reference this one; remove or reassign them before deleting it."
CONTRACT_TITLE = "<b>Esc</b> Contract-7x"
CONTRACT_ESCAPED = "&lt;b&gt;Esc&lt;/b&gt; Contract-7x"


def _formset_frame() -> str:
    import crud_views

    source = Path(crud_views.__file__).parent / "templates" / "crud_views" / "formsets" / "formset.html"
    # the stock frame verbatim behind a sentinel: every structural hook formset.js reads stays in place
    return "<!-- MX-FORMSET {{ x_formset.prefix }} -->" + source.read_text()


OVERRIDES = {
    "crud_views/view_list.content.html": (
        '{% load crud_views %}<dl data-mx="list">{% for object in object_list %}'
        '<dt data-mx-row="{{ object.pk }}">{{ object }}</dt>'
        "<dd>{% for key in view.cv_list_actions %}{% cv_list_action key object %}{% endfor %}</dd>"
        "{% endfor %}</dl><p>MX-LIST-SENTINEL</p>"
    ),
    "crud_views/tags/card.html": (
        "{% load crud_views %}{% cv_card_action_group object as group %}"
        '<details data-mx="card" data-mx-card="{{ object.pk }}" open><summary>MX-CARD {{ object }}</summary>'
        '<form method="get">{% for ctx in group.inline %}'
        '<a data-mx-card-action="{{ ctx.cv_key }}" href="{{ ctx.cv_url }}"'
        '{% if ctx.cv_disabled %} aria-disabled="true"{% endif %}>{{ ctx.cv_label }}</a>'
        "{% endfor %}</form></details>"
    ),
    "crud_views/tags/button/action.html": (
        '<{{ cv_tag }} data-mx-action="{{ cv_key }}" data-mx-location="{{ cv_location }}"'
        '{% if cv_tag == "a" %} href="{{ cv_href }}"{% endif %}{% if cv_disabled %} data-mx-disabled="true"{% endif %}'
        ">MX-ACTION {{ cv_label }}</{{ cv_tag }}>"
    ),
    "crud_views/view_guardian_manage.html": (
        '{% extends "crud_views/view_manage.html" %}{% block guardian_config %}<dl data-mx="manage">'
        "{% for view_key, view in views.items %}<dt>{{ view_key }}</dt>"
        "<dd>{{ view.guardian_policy.effective_policy }}</dd>{% endfor %}</dl>"
        "<p>MX-MANAGE-SENTINEL helper={{ guardian_config.get_objects_for_user }}</p>{% endblock guardian_config %}"
    ),
    "crud_views/tags/alert.html": (
        '<div role="alert" data-mx-alert="{{ alert.level }}"><strong>MX-ALERT {{ alert.heading }}</strong>'
        "{% if alert.text %}<p>{{ alert.text }}</p>{% endif %}"
        "<ul>{% for item in alert.items %}<li>{{ item }}</li>{% endfor %}</ul>"
        '{% if alert.body_template == "crud_views/snippets/delete/related_objects_tree.html" %}'
        "{% include alert.body_template %}{% endif %}</div>"
    ),
}


@pytest.fixture
def native(settings):
    """Locmem overrides of the six native seams in front of the project's loaders; restored by ``settings``."""
    templates = copy.deepcopy(settings.TEMPLATES)
    engine = templates[0]
    engine["APP_DIRS"] = False
    engine["OPTIONS"]["loaders"] = [
        ("django.template.loaders.locmem.Loader", {**OVERRIDES, "crud_views/formsets/formset.html": _formset_frame()}),
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    settings.TEMPLATES = templates
    yield


# ── isolated routes (A08) ─────────────────────────────────────────────────────


@pytest.fixture
def tp(monkeypatch):
    """Fresh routes: Guardian and core Publisher families, and a strict Guardian Book child with create aliases."""
    from crud_views.lib import check as check_module
    from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
    from crud_views.lib.formsets import FormSetMixin, FormSets
    from crud_views.lib.view import CardAction, ContextButton
    from crud_views.lib.views import (
        CardListViewPermissionRequired,
        CreateViewParentMixin,
        DeleteViewPermissionRequired,
        DetailViewPermissionRequired,
        ListViewPermissionRequired,
    )
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ParentViewSet, ViewSet, context_buttons_default
    from crud_views_guardian.lib.views import (
        GuardianCardListViewPermissionRequired,
        GuardianCreateViewPermissionRequired,
        GuardianDeleteViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
        GuardianUpdateViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Book, Publisher
    from tests.test1.app.views import BookForm, PublisherForm

    sfx = uuid.uuid4().hex[:8]
    names = [f"tpg{sfx}", f"tpc{sfx}", f"tpbook{sfx}"]
    modname = f"tests.test1._tp_urls_{sfx}"
    vocab_snapshot = dict(check_module._VOCAB_CACHE)
    state = {"enabled": True}
    state_calls: list = []
    calls = {"render": 0}
    CHOICES["evaluated"] = 0

    original_get_template = FormSets.get_template

    def counting_get_template(self, *args, **kwargs):
        calls["render"] += 1
        return original_get_template(self, *args, **kwargs)

    monkeypatch.setattr(FormSets, "get_template", counting_get_template)

    try:
        g_vs = GuardianViewSet(model=Publisher, name=names[0], icon_header="fa-regular fa-building")

        class TpGList(GuardianListViewPermissionRequired):
            cv_viewset = g_vs

        class TpGCard(GuardianCardListViewPermissionRequired):
            cv_viewset = g_vs
            cv_card_actions = [CardAction(child_name=names[2], child_key="create", label="Add book")]

        class TpGDetail(GuardianDetailViewPermissionRequired):
            cv_viewset = g_vs

        class TpGUpdate(CrispyViewMixin, FormSetMixin, GuardianUpdateViewPermissionRequired):
            form_class = PublisherMainForm
            cv_viewset = g_vs
            cv_formsets = publisher_formsets()

        class TpGDelete(CrispyViewMixin, GuardianDeleteViewPermissionRequired):
            form_class = CrispyDeleteForm
            cv_viewset = g_vs
            cv_show_related_objects = True

        class TpGCreate(CrispyViewMixin, GuardianCreateViewPermissionRequired):
            form_class = PublisherForm
            cv_viewset = g_vs

        c_vs = ViewSet(model=Publisher, name=names[1], icon_header="fa-regular fa-building")

        class TpCList(ListViewPermissionRequired):
            cv_viewset = c_vs

        class TpCCard(CardListViewPermissionRequired):
            cv_viewset = c_vs

        class TpCDetail(DetailViewPermissionRequired):
            cv_viewset = c_vs

        class TpCDelete(CrispyViewMixin, DeleteViewPermissionRequired):
            form_class = CrispyDeleteForm
            cv_viewset = c_vs
            cv_show_related_objects = True

        book_vs = GuardianViewSet(
            model=Book,
            name=names[2],
            parent=ParentViewSet(name=names[0], attribute="publisher"),
            icon_header="fa-regular fa-address-book",
            cv_guardian_parent_permission="view",
            cv_guardian_parent_create_permission="change",
            context_buttons=[
                *context_buttons_default(),
                ContextButton(key="create_alias", key_target="create", label_template_code="Another book"),
            ],
        )
        child_page_actions = ["create", "create_alias"]

        class TpBookList(GuardianListViewPermissionRequired):
            cv_viewset = book_vs

        class TpBookDetail(GuardianDetailViewPermissionRequired):
            cv_viewset = book_vs
            cv_context_actions = child_page_actions

        class TpBookUpdate(CrispyViewMixin, GuardianUpdateViewPermissionRequired):
            form_class = BookForm
            cv_viewset = book_vs
            cv_context_actions = child_page_actions

        class TpBookDelete(CrispyViewMixin, GuardianDeleteViewPermissionRequired):
            form_class = CrispyDeleteForm
            cv_viewset = book_vs
            cv_context_actions = child_page_actions

        class TpBookCard(GuardianCardListViewPermissionRequired):
            cv_viewset = book_vs
            cv_card_actions = [CardAction(key="create", label="Sibling book"), CardAction(key="detail", label="Open")]

        class TpBookCreate(CrispyViewMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired):
            form_class = BookForm
            cv_viewset = book_vs

            @classmethod
            def cv_action_enabled(cls, user, obj=None):
                state_calls.append(obj)  # asserted per test: always the real Publisher parent, never the Book
                return state["enabled"]

        module = types.ModuleType(modname)
        module.urlpatterns = [
            *g_vs.urlpatterns,
            *c_vs.urlpatterns,
            *book_vs.urlpatterns,
            path("", include("tests.test1.project.urls")),
        ]
        sys.modules[modname] = module

        clear_url_caches()
        with override_settings(ROOT_URLCONF=modname):
            clear_url_caches()
            try:
                yield SimpleNamespace(
                    g_vs=g_vs,
                    c_vs=c_vs,
                    book_vs=book_vs,
                    GList=TpGList,
                    GCard=TpGCard,
                    GDetail=TpGDetail,
                    GUpdate=TpGUpdate,
                    GDelete=TpGDelete,
                    BookDetail=TpBookDetail,
                    BookUpdate=TpBookUpdate,
                    BookDelete=TpBookDelete,
                    BookCard=TpBookCard,
                    BookCreate=TpBookCreate,
                    state=state,
                    state_calls=state_calls,
                    calls=calls,
                )
            finally:
                clear_url_caches()
    finally:
        with _REGISTRY_LOCK:
            for name in names:
                _REGISTRY.pop(name, None)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocab_snapshot)
        sys.modules.pop(modname, None)
        clear_url_caches()


@pytest.fixture
def world(db, publisher_a, publisher_b):
    from tests.test1.app.models import Contract

    Contract.objects.create(publisher=publisher_b, title=SECRET)  # only an application choice field lists it
    return SimpleNamespace(a=publisher_a, b=publisher_b)


# ── helpers ───────────────────────────────────────────────────────────────────


def _u(vs, key, pk=None, parent_pk=None):
    kwargs = {}
    if parent_pk is not None:
        kwargs[vs.parent.get_pk_name()] = parent_pk
    if pk is not None:
        kwargs["pk"] = pk
    return reverse(vs.get_router_name(key), kwargs=kwargs)


def _user(name, *, global_perms=(), superuser=False, active=True):
    from django.contrib.auth.models import Permission, User

    if superuser:
        user = User.objects.create_superuser(username=name, password="password")
    else:
        user = User.objects.create_user(username=name, password="password")
    for codename in global_perms:
        user.user_permissions.add(Permission.objects.get(codename=codename))
    if not active:
        user.is_active = False
        user.save()
    return User.objects.get(pk=user.pk)


def _grant(user, vs, obj, *perms):
    from guardian.shortcuts import assign_perm

    for perm in perms:
        assign_perm(vs.permissions[perm], user, obj)


def _instances(value, model, depth=0) -> list:
    """Every ``model`` instance reachable through containers and querysets of a context value."""
    if depth > 8:
        return []
    if isinstance(value, model):
        return [value]
    if isinstance(value, dict):
        return [hit for v in value.values() for hit in _instances(v, model, depth + 1)]
    if isinstance(value, (list, tuple, set, QuerySet)):
        return [hit for v in value for hit in _instances(v, model, depth + 1)]
    return []


def _context_pks(response, model) -> set:
    return {obj.pk for layer in response.context for obj in _instances(layer.flatten(), model)}


def _create_url(tp, world):
    return _u(tp.book_vs, "create", parent_pk=world.a.pk)


def _assert_state_hook_saw_only_parent(tp, publisher):
    from tests.test1.app.models import Publisher

    assert tp.state_calls, "the create state hook was not consulted"
    assert all(type(obj) is Publisher and obj.pk == publisher.pk for obj in tp.state_calls), tp.state_calls


# ── list content: enumerates only the library's object_list ───────────────────


@pytest.mark.django_db
def test_list_override_enumerates_only_permitted_rows(native, tp, client, world):
    from tests.test1.app.models import Publisher

    escaped = Publisher.objects.create(name="<i>Esc Pub</i>")
    user = _user("lister")
    _grant(user, tp.g_vs, world.a, "view")
    _grant(user, tp.g_vs, escaped, "view")
    client.force_login(user)

    response = client.get(_u(tp.g_vs, "list"))
    assert response.status_code == 200
    content = response.content.decode()
    assert "MX-LIST-SENTINEL" in content
    assert sorted(re.findall(r'data-mx-row="(\d+)"', content)) == sorted([str(world.a.pk), str(escaped.pk)])
    assert "Gollancz" not in content
    assert _context_pks(response, Publisher) == {world.a.pk, escaped.pk}  # the denied row never reaches context
    assert "&lt;i&gt;Esc Pub&lt;/i&gt;" in content and "<i>Esc Pub</i>" not in content  # literal escaping kept
    assert "MX-ACTION" in content  # row actions render through the overridden leaf


@pytest.mark.django_db
def test_list_override_denied_requests_receive_no_rows(native, tp, client, world):
    from tests.test1.app.models import Publisher

    # Guardian, active but ungranted: the page renders, the library hands over an empty object_list
    client.force_login(_user("ungranted"))
    response = client.get(_u(tp.g_vs, "list"))
    assert response.status_code == 200
    assert "MX-LIST-SENTINEL" in response.content.decode()
    assert 'data-mx-row="' not in response.content.decode()
    assert _context_pks(response, Publisher) == set()

    # core without the global view permission: no page at all
    response = client.get(_u(tp.c_vs, "list"))
    assert response.status_code == 403
    assert "MX-LIST-SENTINEL" not in response.content.decode()

    # inactive superuser through a backend that keeps the session: 403 before any row is fetched
    with override_settings(AUTHENTICATION_BACKENDS=INACTIVE_BACKENDS):
        client.force_login(_user("inactive_root", superuser=True, active=False), backend=ALLOW_INACTIVE)
        response = client.get(_u(tp.g_vs, "list"))
    assert response.status_code == 403
    assert "MX-LIST-SENTINEL" not in response.content.decode()
    assert "Pan Books" not in response.content.decode()


@pytest.mark.django_db
def test_core_list_override_shows_all_rows_to_global_viewer(native, tp, client, world):
    from tests.test1.app.models import Publisher

    client.force_login(_user("global_viewer", global_perms=["view_publisher"]))
    response = client.get(_u(tp.c_vs, "list"))
    assert response.status_code == 200
    assert set(re.findall(r'data-mx-row="(\d+)"', response.content.decode())) == {str(world.a.pk), str(world.b.pk)}
    assert _context_pks(response, Publisher) == {world.a.pk, world.b.pk}


# ── card: consumes the resolved object and card action group ──────────────────


@pytest.mark.parametrize("create_grant", [True, False])
@pytest.mark.django_db
def test_card_override_consumes_resolved_rows_and_actions(native, tp, client, world, create_grant):
    from tests.test1.app.models import Publisher

    user = _user("carder")
    _grant(user, tp.g_vs, world.a, "view", *(["change"] if create_grant else []))
    client.force_login(user)

    response = client.get(_u(tp.g_vs, "card"))
    assert response.status_code == 200
    content = response.content.decode()
    assert re.findall(r'data-mx-card="(\d+)"', content) == [str(world.a.pk)]
    assert "MX-CARD Pan Books" in content and "Gollancz" not in content
    assert _context_pks(response, Publisher) == {world.a.pk}
    create_url = _create_url(tp, world)
    assert (f'href="{create_url}">Add book</a>' in content) is create_grant
    assert "Add book" in content if create_grant else "Add book" not in content


@pytest.mark.parametrize(("create_grant", "enabled"), [(True, True), (False, True), (True, False)])
@pytest.mark.django_db
def test_child_card_create_action_uses_row_parent(native, tp, client, world, create_grant, enabled):
    """H03: a Book row's own-child create action resolves its FK parent; permission and state stay separate."""
    from tests.test1.app.models import Book

    book = Book.objects.create(title="Card Child", publisher=world.a)
    tp.state["enabled"] = enabled
    user = _user("child_carder")
    _grant(user, tp.g_vs, world.a, "view", *(["change"] if create_grant else []))
    _grant(user, tp.book_vs, book, "view")
    client.force_login(user)

    response = client.get(_u(tp.book_vs, "card", parent_pk=world.a.pk))
    assert response.status_code == 200
    content = response.content.decode()
    assert "MX-CARD Card Child" in content
    assert f'href="{_u(tp.book_vs, "detail", book.pk, world.a.pk)}">Open</a>' in content
    assert (f'href="{_create_url(tp, world)}">Sibling book</a>' in content) is (create_grant and enabled)
    _assert_state_hook_saw_only_parent(tp, world.a)


# ── action leaf: toolbar create, alias and the permission filter on child pages (H03) ──


def _child_page_actor(tp, world, child, *, create_grant, name="page_actor"):
    user = _user(name)
    _grant(user, tp.g_vs, world.a, "view", *(["change"] if create_grant else []))
    _grant(user, tp.book_vs, child, "view", "change", "delete")
    return user


@pytest.fixture
def child(world):
    from tests.test1.app.models import Book

    return Book.objects.create(title="Child Page Book", publisher=world.a)


def _render_filter_and_button(response):
    view = response.context["view"]
    template = Template(
        '{% load crud_views %}{{ view|cv_context_has_permission:"create" }}|{% cv_context_button "create" %}'
    )
    return template.render(Context({"view": view, "request": view.request})).split("|", 1)


@pytest.mark.parametrize("condition", ["permitted", "denied", "disabled"])
@pytest.mark.parametrize("page", ["detail", "update", "delete"])
@pytest.mark.django_db
def test_child_page_toolbar_create_and_alias_through_action_leaf(
    native, tp, client, monkeypatch, world, child, page, condition
):
    from tests.test1.app.models import Book

    tp.state["enabled"] = condition != "disabled"
    client.force_login(_child_page_actor(tp, world, child, create_grant=condition != "denied"))
    create_url = _create_url(tp, world)
    allowed = condition == "permitted"

    response = client.get(_u(tp.book_vs, page, child.pk, world.a.pk))
    assert response.status_code == 200
    content = response.content.decode()
    assert "MX-ACTION" in content  # the toolbar renders through the overridden leaf
    assert content.count(f'href="{create_url}"') == (2 if allowed else 0)  # the create key and its alias
    assert ("MX-ACTION Another book" in content) is allowed  # the alias keeps its own label
    assert "Child Page Book" in content  # the page's own child context is unchanged

    permission, button = _render_filter_and_button(response)
    assert permission == str(condition != "denied")  # permission-only: True for an authorized disabled parent
    assert ("MX-ACTION" in button and create_url in button) is allowed
    _assert_state_hook_saw_only_parent(tp, world.a)

    before = Book.objects.count()
    assert client.get(create_url).status_code == (200 if allowed else 403)
    assert client.post(create_url, {"title": "Toolbar Child"}).status_code == (302 if allowed else 403)
    assert Book.objects.count() == before + (1 if allowed else 0)


@pytest.mark.django_db
def test_child_page_disable_mode_renders_denied_create_as_disabled(native, tp, client, monkeypatch, world, child):
    monkeypatch.setattr(tp.BookCreate, "cv_inaccessible_actions", "disable")
    client.force_login(_child_page_actor(tp, world, child, create_grant=False))
    create_url = _create_url(tp, world)

    response = client.get(_u(tp.book_vs, "detail", child.pk, world.a.pk))
    assert response.status_code == 200
    content = response.content.decode()
    assert 'data-mx-disabled="true"' in content  # shown, but as a disabled control
    assert f'href="{create_url}"' not in content
    assert client.get(create_url).status_code == 403


# ── manage: per-view policy through the overridden page, under the group gate (A20) ──


@pytest.fixture
def manage_mode(monkeypatch):
    from crud_views.lib.settings import crud_views_settings

    def set_mode(mode):
        monkeypatch.setattr(crud_views_settings, "manage_views_enabled", mode)
        monkeypatch.setattr(crud_views_settings, "manage_group", MANAGE_GROUP)
        assert (crud_views_settings.manage_views_enabled, crud_views_settings.manage_group) == (mode, MANAGE_GROUP)

    return set_mode


@pytest.mark.parametrize(
    ("mode", "debug", "actor", "status"),
    [
        ("no", False, "group", 200),
        ("no", False, "nongroup", 403),
        ("no", False, "anonymous", 302),
        ("debug_only", False, "group", 200),
        ("debug_only", False, "nongroup", 403),
        ("debug_only", True, "nongroup", 200),
    ],
)
@pytest.mark.django_db
def test_manage_override_shows_mixed_policy_only_when_authorized(
    native, tp, client, monkeypatch, manage_mode, world, mode, debug, actor, status
):
    from django.contrib.auth.models import Group

    monkeypatch.setattr(tp.GDetail, "cv_guardian_accept_global_perms", True)  # list stays strict: mixed policy
    manage_mode(mode)
    if actor != "anonymous":
        user = _user(f"manage_{actor}")
        if actor == "group":
            user.groups.add(Group.objects.get_or_create(name=MANAGE_GROUP)[0])
        client.force_login(user)
    with override_settings(DEBUG=debug):
        response = client.get(_u(tp.g_vs, "manage"))

    assert response.status_code == status
    content = response.content.decode()
    if status != 200:
        assert "MX-MANAGE-SENTINEL" not in content
        if status == 302:
            assert response["Location"].startswith(LOGIN)
        return
    assert "MX-MANAGE-SENTINEL" in content
    policies = dict(re.findall(r"<dt>(\w+)</dt><dd>([^<]*)</dd>", content))
    assert policies["list"] == "strict"
    assert policies["detail"] == "global fallback"
    assert policies["create"] == "not applicable"
    assert "accept_global_perms" in content.split("MX-MANAGE-SENTINEL", 1)[1]  # the strict helper policy


# ── alert: one generic blocked notice, only permitted protected labels ────────


@pytest.mark.parametrize("label_visible", [False, True])
@pytest.mark.parametrize("family", ["core", "guardian"])
@pytest.mark.django_db
def test_alert_override_receives_only_permitted_protected_labels(native, tp, client, world, family, label_visible):
    from tests.test1.app.models import Contract, Publisher

    contract = Contract.objects.create(publisher=world.a, title=CONTRACT_TITLE)
    if family == "core":
        perms = ["delete_publisher", *(["view_contract"] if label_visible else [])]
        user = _user("deleter", global_perms=perms)
        vs = tp.c_vs
    else:
        from guardian.shortcuts import assign_perm

        user = _user("deleter")
        _grant(user, tp.g_vs, world.a, "delete")
        if label_visible:
            assign_perm(f"{Contract._meta.app_label}.view_contract", user, contract)
        vs = tp.g_vs
    client.force_login(user)

    response = client.get(_u(vs, "delete", world.a.pk))
    assert response.status_code == 200
    content = response.content.decode()
    assert content.count(f"MX-ALERT {BLOCKED_HEADING}") == 1  # one generic notice, whatever is hidden
    assert content.count("<strong>MX-ALERT ") == 1  # protected-only: no related-summary alerts
    assert response.context["has_protected_objects"] is True
    assert response.context["related_summary"] == {}
    blocked = content.split(f"MX-ALERT {BLOCKED_HEADING}", 1)[1].split("</div>", 1)[0]
    if label_visible:
        assert f"<strong>MX-ALERT {BLOCKED_LIST_HEADING}</strong>" in content
        assert BLOCKED_SENTENCE not in content
        assert re.findall(r"<li>(.*?)</li>", blocked) == [CONTRACT_ESCAPED]  # literal escaping kept
        assert response.context["protected_objects"] == [contract]
    else:
        assert f"<strong>MX-ALERT {BLOCKED_HEADING}</strong>" in content
        assert BLOCKED_LIST_HEADING not in content
        assert content.count(BLOCKED_SENTENCE) == 1
        assert "<li>" not in blocked  # no placeholder per hidden object
        assert response.context["protected_objects"] == []
        assert _context_pks(response, Contract) == set()
        assert CONTRACT_ESCAPED not in content
    assert CONTRACT_TITLE not in content
    assert "<form" not in content
    assert Publisher.objects.filter(pk=world.a.pk).exists()


@pytest.mark.parametrize("family", ["core", "guardian"])
@pytest.mark.django_db
def test_alert_override_absent_for_denied_delete_page(native, tp, client, world, family):
    from tests.test1.app.models import Contract

    Contract.objects.create(publisher=world.a, title=CONTRACT_TITLE)
    client.force_login(_user("viewer_only", global_perms=["view_contract"]))
    response = client.get(_u(tp.c_vs if family == "core" else tp.g_vs, "delete", world.a.pk))
    assert response.status_code == 403
    assert "MX-ALERT" not in response.content.decode()
    assert CONTRACT_ESCAPED not in response.content.decode()


# ── formset frame: structural hooks, authorized choices, nested fragments ─────


@pytest.mark.django_db
def test_formset_override_serves_authorized_editor_and_fragments(native, tp, client, world):
    from tests.test1.app.models import Book

    book = Book.objects.create(title="Formset Book", publisher=world.a)
    user = _user("editor")
    _grant(user, tp.g_vs, world.a, "view", "change")
    client.force_login(user)
    update_url = _u(tp.g_vs, "update", world.a.pk)

    page = client.get(update_url)
    assert page.status_code == 200
    content = page.content.decode()
    assert f"MX-FORMSET books-{world.a.pk}-0" in content
    for hook in ("cv-data-formset=", "cv-data-formset-prefix=", "cv-formset-row", f"books-{world.a.pk}-0-TOTAL_FORMS"):
        assert hook in content, hook
    assert SECRET in content  # D-13: an authorized editor keeps the application's ordinary choices

    top = client.get(update_url, {"template": "books", "num": "1", "pk": str(world.a.pk)})
    assert top.status_code == 200
    data = top.json()
    assert set(data) == {"html", "rows"}
    assert data["rows"] == [f"books-{world.a.pk}-0-1"]
    assert "MX-FORMSET" in data["html"] and f'name="{data["rows"][0]}-title"' in data["html"]

    nested = client.get(
        update_url,
        {"template": "books|notes", "num": "1", "pk": str(book.pk), "formset_parent_prefix_key": f"{world.a.pk}-0-0"},
    )
    assert nested.status_code == 200
    data = nested.json()
    assert set(data) == {"html", "rows"}
    (row,) = data["rows"]
    assert row.startswith("books-notes-") and f'name="{row}-note"' in data["html"]
    assert "MX-FORMSET" in data["html"]


@pytest.mark.django_db
def test_formset_override_never_reached_by_denied_editor(native, tp, client, world):
    user = _user("viewer")
    _grant(user, tp.g_vs, world.a, "view")  # may open the detail page, not the editor
    client.force_login(user)
    update_url = _u(tp.g_vs, "update", world.a.pk)

    assert client.get(_u(tp.g_vs, "detail", world.a.pk)).status_code == 200
    for response in (
        client.get(update_url),
        client.get(update_url, {"template": "books", "num": "1", "pk": str(world.a.pk)}),
    ):
        assert response.status_code == 403
        assert b"MX-FORMSET" not in response.content
        assert SECRET.encode() not in response.content
    assert tp.calls["render"] == 0
    assert CHOICES["evaluated"] == 0


@pytest.mark.django_db
@pytest.mark.parametrize("family", ["core", "guardian"])
@pytest.mark.parametrize("visibility", ["hidden", "partial", "full", "group", "global-strict", "global-fallback"])
@pytest.mark.parametrize("modal", [False, True])
@pytest.mark.parametrize("details", [False, True])
@pytest.mark.parametrize("business", [False, True])
def test_partial_native_template_context_shape(
    native, tp, client, world, monkeypatch, family, visibility, modal, details, business
):
    """Native and provider rows share projection; root/None/tree shape and numeric partial counts survive."""
    from django.contrib.auth.models import Group
    from django.utils.html import escape
    from guardian.shortcuts import assign_perm

    from crud_views.lib.deletion import DeletePreviewContribution
    from tests.test1.app.models import Book, Contract, Publisher

    vs = tp.c_vs if family == "core" else tp.g_vs
    view = vs.get_view_class("delete")
    events = []
    native_book = Book.objects.create(publisher=world.a, title="<b>Native</b> Bücher 東京")
    provider_book = Book.objects.create(publisher=world.b, title="<i>Provider</i> Étoile 雪")
    native_blocker = Contract.objects.create(publisher=world.a, title="<u>Native</u> Vertrag Ω")
    provider_blocker = Contract.objects.create(publisher=world.b, title="<s>Provider</s> عقد")

    def delete(self, *, using):
        events.append("delete")
        raise AssertionError("known protection must precede the actual model delete")

    def provider(self, boundaries, *, using):
        assert using == "default"
        assert len(boundaries) == 1 and boundaries[0].kind == "model_delete"
        return [DeletePreviewContribution(boundaries[0], deleted=(provider_book,), protected=(provider_blocker,))]

    monkeypatch.setattr(Publisher, "delete", delete)
    monkeypatch.setattr(view, "cv_get_delete_preview", provider)
    monkeypatch.setattr(view, "cv_show_related_objects", details)
    monkeypatch.setattr(view, "cv_modal", True)
    monkeypatch.setattr(view, "cv_check_delete_protection", lambda self: ["Business veto"] if business else [])
    monkeypatch.setattr(view, "cv_form_valid_hook", lambda *args: events.append("hook"))
    monkeypatch.setattr(view, "cv_on_commit", lambda *args: events.append("commit"))
    if family == "guardian":
        monkeypatch.setattr(view, "cv_guardian_accept_global_perms", visibility == "global-fallback")

    globals_ = ["delete_publisher"] if family == "core" else []
    if (family == "core" and visibility != "hidden") or visibility.startswith("global"):
        globals_ += ["view_book"]
        if visibility != "partial":
            globals_ += ["view_contract"]
    user = _user("partial_context", global_perms=globals_)
    if family == "guardian":
        _grant(user, vs, world.a, "delete")
        if visibility in {"partial", "full", "group"}:
            principal = user
            if visibility == "group":
                principal = Group.objects.create(name="partial_preview_readers")
                user.groups.add(principal)
            for obj in [
                native_book,
                native_blocker,
                *([provider_book, provider_blocker] if visibility != "partial" else []),
            ]:
                assign_perm(f"view_{obj._meta.model_name}", principal, obj)
    client.force_login(user)
    headers = {"X-CV-Modal": "true"} if modal else {}
    url = _u(vs, "delete", world.a.pk)

    books = []
    blockers = []
    if family == "core":
        if visibility != "hidden":
            books = [native_book, provider_book]
        if visibility not in {"hidden", "partial"}:
            blockers = [native_blocker, provider_blocker]
    elif visibility in {"full", "group", "global-fallback"}:
        books, blockers = [native_book, provider_book], [native_blocker, provider_blocker]
    elif visibility == "partial":
        books, blockers = [native_book], [native_blocker]

    for method, data, status in [
        ("get", {}, 200),
        ("get", {}, 200),
        ("post", {}, 422 if modal else 200),
        ("post", {"confirm": True}, 422 if modal else 200),
    ]:
        response = getattr(client, method)(url, data, headers=headers)
        assert response.status_code == status
        context = response.context
        assert context["delete_preview_incomplete"] is True
        assert context["has_protected_objects"] is True
        content = response.content.decode()
        assert "This preview is incomplete." in content
        assert "MX-ALERT" in content and "<form" not in content
        assert ("Business veto" in content) is business
        if details:
            assert context["related_summary"] == {"book": 2}
            assert all(
                isinstance(name, str) and type(count) is int for name, count in context["related_summary"].items()
            )
            assert ("partial counts" in content) is not business
            assert context["protected_objects"] == blockers
            (root,) = context["related_objects"]
            assert root["obj"] is None and root["url"] is None
            assert [node["obj"] for node in root["children"]] == [
                obj if obj in books else None for obj in (native_book, provider_book)
            ]
        else:
            for key in ("related_summary", "related_objects", "protected_objects"):
                assert key not in context
            assert "partial counts" not in content
        assert _context_pks(response, Book) == ({obj.pk for obj in books} if details else set())
        assert _context_pks(response, Contract) == ({obj.pk for obj in blockers} if details else set())
        for obj in (native_book, provider_book, native_blocker, provider_blocker):
            assert str(obj) not in content
            assert (str(escape(str(obj))) in content) is (details and not business and obj in [*books, *blockers])
        if details and not blockers and not business:
            assert BLOCKED_SENTENCE in content
            assert BLOCKED_LIST_HEADING not in content
        assert events == []
        assert Publisher.objects.filter(pk=world.a.pk).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "actor", ["anonymous", "ungranted", "revoked", "inactive", "wrong-parent", "disabled", "allowed"]
)
def test_partial_delete_request_gates_precede_inspector(native, tp, client, world, child, monkeypatch, actor):
    """The new provider is unreachable through denied parent/object/state and forbidden method paths."""
    from guardian.shortcuts import remove_perm

    events = []

    def forbidden(*args, **kwargs):
        events.append("unexpected callback")
        raise AssertionError("request gate must precede inspection and mutation")

    for name in ("cv_get_delete_preview", "cv_post_hook", "cv_form_valid", "cv_form_valid_hook", "cv_on_commit"):
        monkeypatch.setattr(tp.BookDelete, name, forbidden)
    if actor != "anonymous":
        user = _user("gated_delete", active=actor != "inactive")
        _grant(user, tp.g_vs, world.a, "view")
        _grant(user, tp.g_vs, world.b, "view")
        if actor != "ungranted":
            _grant(user, tp.book_vs, child, "delete")
        if actor == "revoked":
            remove_perm(tp.book_vs.permissions["delete"], user, child)
        client.force_login(user, backend=ALLOW_INACTIVE)
    if actor == "disabled":
        monkeypatch.setattr(tp.BookDelete, "cv_action_enabled", classmethod(lambda cls, user, obj=None: False))
    url = _u(tp.book_vs, "delete", child.pk, world.b.pk if actor == "wrong-parent" else world.a.pk)
    with override_settings(AUTHENTICATION_BACKENDS=INACTIVE_BACKENDS):
        if actor == "allowed":
            response = client.delete(url)
            assert response.status_code == 405
            assert "DELETE" not in response["Allow"]
            response = client.options(url)
            assert response.status_code == 200 and "DELETE" not in response["Allow"]
        else:
            status = 302 if actor == "anonymous" else 404 if actor == "wrong-parent" else 403
            for method in ("get", "post"):
                response = getattr(client, method)(url, {"confirm": True})
                assert response.status_code == status
                assert b"MX-ALERT" not in response.content
    assert events == []
    assert type(child).objects.filter(pk=child.pk).exists()
