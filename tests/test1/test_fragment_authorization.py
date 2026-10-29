"""Phase 6.2 B2 (AUTH-02, D-09/D-12/D-13): formset fragment requests authorize the real target first.

A fragment request (``GET ?template=...``) used to be answered by ``FormSetMixinBase.get()`` before the view loaded
its object. Guardian object views authorize in ``get_object()``, so an actor without a grant on the object received
the editor's row HTML, including the choices of every custom ``ModelChoiceField`` (here: a secret Contract title).

These tests drive real registered routes (fresh ViewSets, a temporary ROOT_URLCONF, registry, vocabulary and URL
cache cleanup in ``finally``; A08). Denied requests must never reach fragment rendering or choice evaluation. The
browser payload positives derive their query from the rendered ``cv-data-formset`` metadata the way ``formset.js``
builds it (A06) and assert exact ``rows``, usable ``html`` and no database writes.
"""

import json
import re
import sys
import types
import uuid
from collections import OrderedDict
from types import SimpleNamespace

import pytest
from crispy_forms.layout import Row
from django import forms
from django.forms.models import ModelChoiceIterator, inlineformset_factory
from django.test import Client, override_settings
from django.urls import clear_url_caches, include, path, reverse
from lxml import html as lxml_html

from crud_views.lib.crispy import Column4, CrispyModelForm
from crud_views.lib.formsets import FormSet, FormSets, Formsets, InlineFormSet
from tests.test1.app.models import Book, BookNote, Contract, Publisher

SECRET = "TOP-SECRET-CONTRACT-7f3a"
ALLOW_INACTIVE = "django.contrib.auth.backends.AllowAllUsersModelBackend"

# Every evaluation of a secret choice list is counted: a denied request must leave this at zero.
CHOICES = {"evaluated": 0}


class _CountingChoiceIterator(ModelChoiceIterator):
    def __iter__(self):
        CHOICES["evaluated"] += 1
        yield from super().__iter__()


class SecretChoiceField(forms.ModelChoiceField):
    """An ordinary application ModelChoiceField over all Contracts (D-13: its filtering is the app's concern)."""

    iterator = _CountingChoiceIterator


class SecretBookForm(CrispyModelForm):
    contract = SecretChoiceField(queryset=Contract.objects.all(), required=False)

    class Meta:
        model = Book
        fields = ["title"]


class SecretBookInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        return [Row(Column4("title"), Column4("contract"), self.form_control_col4)]


class SecretNoteForm(CrispyModelForm):
    contract = SecretChoiceField(queryset=Contract.objects.all(), required=False)

    class Meta:
        model = BookNote
        fields = ["note"]


class SecretNoteInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        return [Row(Column4("note"), Column4("contract"), self.form_control_col4)]


SecretBookFormSet = inlineformset_factory(
    Publisher,
    Book,
    formset=SecretBookInlineFormSet,
    form=SecretBookForm,
    fields=["title"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)

SecretNoteFormSet = inlineformset_factory(
    Book,
    BookNote,
    formset=SecretNoteInlineFormSet,
    form=SecretNoteForm,
    fields=["note"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)


def publisher_formsets() -> FormSets:
    return FormSets(
        formsets=OrderedDict(
            books=FormSet(
                title="Books",
                klass=SecretBookFormSet,
                children=OrderedDict(notes=FormSet(title="Notes", klass=SecretNoteFormSet)),
            )
        )
    )


def book_formsets() -> FormSets:
    return FormSets(formsets=OrderedDict(notes=FormSet(title="Notes", klass=SecretNoteFormSet)))


class PublisherMainForm(CrispyModelForm):
    class Meta:
        model = Publisher
        fields = ["name"]

    def get_layout_fields(self):
        return [Row(Column4("name")), Formsets()]

    @property
    def helper(self):
        h = super().helper
        h.form_tag = False
        return h


class BookMainForm(CrispyModelForm):
    class Meta:
        model = Book
        fields = ["title"]

    def get_layout_fields(self):
        return [Row(Column4("title")), Formsets()]

    @property
    def helper(self):
        h = super().helper
        h.form_tag = False
        return h


# ── isolated routes (A08) ─────────────────────────────────────────────────────


@pytest.fixture
def fr(monkeypatch):
    """Fresh Guardian Publisher/Book (nested) and core Publisher routes with secret-choice formsets."""
    from crud_views.lib import check as check_module
    from crud_views.lib.crispy import CrispyViewMixin
    from crud_views.lib.formsets import FormSetMixin
    from crud_views.lib.views import (
        CreateViewParentMixin,
        CreateViewPermissionRequired,
        DetailViewPermissionRequired,
        ListViewPermissionRequired,
        UpdateViewPermissionRequired,
    )
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ParentViewSet, ViewSet
    from crud_views_guardian.lib.views import (
        GuardianCreateViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
        GuardianUpdateViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet

    sfx = uuid.uuid4().hex[:8]
    names = [f"frgpub{sfx}", f"frgbook{sfx}", f"frcpub{sfx}"]
    modname = f"tests.test1._fragment_urls_{sfx}"
    vocab_snapshot = dict(check_module._VOCAB_CACHE)
    calls = {"render": 0}
    CHOICES["evaluated"] = 0

    original_get_template = FormSets.get_template

    def counting_get_template(self, *args, **kwargs):
        calls["render"] += 1
        return original_get_template(self, *args, **kwargs)

    monkeypatch.setattr(FormSets, "get_template", counting_get_template)

    try:
        gpub_vs = GuardianViewSet(model=Publisher, name=names[0], icon_header="fa-regular fa-building")

        class FrGPublisherListView(GuardianListViewPermissionRequired):
            cv_viewset = gpub_vs

        class FrGPublisherDetailView(GuardianDetailViewPermissionRequired):
            cv_viewset = gpub_vs

        class FrGPublisherCreateView(CrispyViewMixin, FormSetMixin, GuardianCreateViewPermissionRequired):
            form_class = PublisherMainForm
            cv_viewset = gpub_vs
            cv_formsets = publisher_formsets()

        class FrGPublisherUpdateView(CrispyViewMixin, FormSetMixin, GuardianUpdateViewPermissionRequired):
            form_class = PublisherMainForm
            cv_viewset = gpub_vs
            cv_formsets = publisher_formsets()

        gbook_vs = GuardianViewSet(
            model=Book,
            name=names[1],
            parent=ParentViewSet(name=names[0], attribute="publisher"),
            icon_header="fa-regular fa-address-book",
        )

        class FrGBookListView(GuardianListViewPermissionRequired):
            cv_viewset = gbook_vs

        class FrGBookDetailView(GuardianDetailViewPermissionRequired):
            cv_viewset = gbook_vs

        class FrGBookCreateView(
            CrispyViewMixin, FormSetMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired
        ):
            form_class = BookMainForm
            cv_viewset = gbook_vs
            cv_formsets = book_formsets()

        class FrGBookUpdateView(CrispyViewMixin, FormSetMixin, GuardianUpdateViewPermissionRequired):
            form_class = BookMainForm
            cv_viewset = gbook_vs
            cv_formsets = book_formsets()

        cpub_vs = ViewSet(model=Publisher, name=names[2], icon_header="fa-regular fa-building")

        class FrCPublisherListView(ListViewPermissionRequired):
            cv_viewset = cpub_vs

        class FrCPublisherDetailView(DetailViewPermissionRequired):
            cv_viewset = cpub_vs

        class FrCPublisherCreateView(CrispyViewMixin, FormSetMixin, CreateViewPermissionRequired):
            form_class = PublisherMainForm
            cv_viewset = cpub_vs
            cv_formsets = publisher_formsets()

        class FrCPublisherUpdateView(CrispyViewMixin, FormSetMixin, UpdateViewPermissionRequired):
            form_class = PublisherMainForm
            cv_viewset = cpub_vs
            cv_formsets = publisher_formsets()

        module = types.ModuleType(modname)
        module.urlpatterns = [
            *gpub_vs.urlpatterns,
            *gbook_vs.urlpatterns,
            *cpub_vs.urlpatterns,
            path("", include("tests.test1.project.urls")),
        ]
        sys.modules[modname] = module

        clear_url_caches()
        with override_settings(ROOT_URLCONF=modname):
            clear_url_caches()
            try:
                yield SimpleNamespace(
                    gpub_vs=gpub_vs,
                    gbook_vs=gbook_vs,
                    cpub_vs=cpub_vs,
                    GPublisherCreate=FrGPublisherCreateView,
                    GPublisherUpdate=FrGPublisherUpdateView,
                    GBookCreate=FrGBookCreateView,
                    GBookUpdate=FrGBookUpdateView,
                    CPublisherUpdate=FrCPublisherUpdateView,
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
def world(db):
    publisher_a = Publisher.objects.create(name="Pan Books")
    publisher_b = Publisher.objects.create(name="Gollancz")
    book_a = Book.objects.create(title="Hitchhiker's Guide", publisher=publisher_a)
    book_b = Book.objects.create(title="Mort", publisher=publisher_b)
    Contract.objects.create(publisher=publisher_b, title=SECRET)
    return SimpleNamespace(publisher_a=publisher_a, publisher_b=publisher_b, book_a=book_a, book_b=book_b)


# ── helpers ────────────────────────────────────────────────────────────────────


def _user(username, *, superuser=False):
    from django.contrib.auth.models import User

    if superuser:
        return User.objects.create_superuser(username=username, password="password")
    return User.objects.create_user(username=username, password="password")


def _grant(user, viewset, obj, *perms):
    from guardian.shortcuts import assign_perm

    for perm in perms:
        assign_perm(viewset.permissions[perm], user, obj)


def _model_perms(user, *codenames):
    from django.contrib.auth.models import Permission

    for codename in codenames:
        user.user_permissions.add(Permission.objects.get(codename=codename))


def _client(user=None, backend=None) -> Client:
    client = Client(raise_request_exception=False)
    if user is not None:
        client.force_login(user, backend=backend)
    return client


def _url(viewset, key, **kwargs):
    return reverse(viewset.get_router_name(key), kwargs=kwargs)


def _get(client, url, params, modal=False):
    headers = {"X-CV-Modal": "true"} if modal else {}
    return client.get(url, params, headers=headers)


def _counts():
    return (Publisher.objects.count(), Book.objects.count(), BookNote.objects.count(), Contract.objects.count())


def _assert_not_rendered(fr, response):
    assert fr.calls["render"] == 0
    assert CHOICES["evaluated"] == 0
    assert SECRET.encode() not in response.content


def _formset_metadata(content: bytes) -> dict:
    """prefix -> (cv-data-formset JSON, TOTAL_FORMS) for every formset container in a rendered page/fragment."""
    doc = lxml_html.fromstring(content)
    out = {}
    for el in doc.cssselect("[cv-data-formset]"):
        data = json.loads(el.get("cv-data-formset"))
        total = doc.cssselect(f'input[name="{data["prefix"]}-TOTAL_FORMS"]')
        out[data["prefix"]] = (data, int(total[0].get("value")) if total else None)
    return out


def browser_add_row(content: bytes, formset_prefix: str, num: int | None = None) -> dict:
    """The add-row query formset.js sends for ``formset_prefix`` (XFormset/XForm.add)."""
    data, total = _formset_metadata(content)[formset_prefix]
    match = re.match(rf"^(?:(.*)-)?(None|{data['pk']})-(\d+)$", data["prefix_key"])
    assert match, data["prefix_key"]
    return {
        "template": "|".join(data["hierarchy"]),
        "pk": match.group(2),
        "num": str(total if num is None else num),
        "formset_parent_prefix_key": data["parent_prefix_key"],
    }


def _assert_fragment(response, expected_rows, fields):
    assert response.status_code == 200, response.content[:500]
    data = response.json()
    assert set(data) == {"html", "rows"}
    assert data["rows"] == expected_rows
    for row in expected_rows:
        for field in fields:
            assert f'name="{row}-{field}"' in data["html"]
    return data


# ── B2 reproduction: Guardian update fragments disclose choices without a grant ──


@pytest.mark.parametrize("modal", [False, True])
@pytest.mark.django_db
def test_ungranted_guardian_update_fragment_denied_before_rendering(fr, world, modal):
    actor = _user("ungranted")
    response = _get(
        _client(actor),
        _url(fr.gpub_vs, "update", pk=world.publisher_a.pk),
        {"template": "books", "pk": str(world.publisher_a.pk), "num": "1", "formset_parent_prefix_key": ""},
        modal=modal,
    )
    # B2: the secret choice label must not cross to an actor who may not open the editor
    assert SECRET.encode() not in response.content
    assert response.status_code == 403
    _assert_not_rendered(fr, response)


@pytest.mark.django_db
def test_ungranted_guardian_update_nested_fragment_denied_before_rendering(fr, world):
    actor = _user("ungranted_nested")
    pa, ba = world.publisher_a, world.book_a
    response = _get(
        _client(actor),
        _url(fr.gpub_vs, "update", pk=pa.pk),
        {"template": "books|notes", "pk": str(ba.pk), "num": "1", "formset_parent_prefix_key": f"{pa.pk}-0-0"},
    )
    assert response.status_code == 403
    _assert_not_rendered(fr, response)


@pytest.mark.django_db
def test_view_only_guardian_actor_is_not_an_editor(fr, world):
    """A view grant opens the detail page, not the editor's fragments."""
    actor = _user("viewer")
    _grant(actor, fr.gpub_vs, world.publisher_a, "view")
    client = _client(actor)
    assert client.get(_url(fr.gpub_vs, "detail", pk=world.publisher_a.pk)).status_code == 200
    response = _get(
        client,
        _url(fr.gpub_vs, "update", pk=world.publisher_a.pk),
        {"template": "books", "pk": str(world.publisher_a.pk), "num": "1", "formset_parent_prefix_key": ""},
    )
    assert response.status_code == 403
    _assert_not_rendered(fr, response)


@pytest.mark.django_db
def test_grant_on_other_object_does_not_open_this_fragment(fr, world):
    actor = _user("other_grant")
    _grant(actor, fr.gpub_vs, world.publisher_b, "view", "change")
    response = _get(
        _client(actor),
        _url(fr.gpub_vs, "update", pk=world.publisher_a.pk),
        {"template": "books", "pk": str(world.publisher_a.pk), "num": "1", "formset_parent_prefix_key": ""},
    )
    assert response.status_code == 403
    _assert_not_rendered(fr, response)


@pytest.mark.parametrize("modal", [False, True])
@pytest.mark.django_db
def test_revoked_guardian_grant_denies_next_fragment(fr, world, modal):
    from guardian.shortcuts import remove_perm

    actor = _user("revoked")
    _grant(actor, fr.gpub_vs, world.publisher_a, "view", "change")
    client = _client(actor)
    url = _url(fr.gpub_vs, "update", pk=world.publisher_a.pk)
    params = {"template": "books", "pk": str(world.publisher_a.pk), "num": "1", "formset_parent_prefix_key": ""}

    _assert_fragment(_get(client, url, params, modal=modal), [f"books-{world.publisher_a.pk}-0-1"], ["title"])

    remove_perm(fr.gpub_vs.permissions["change"], actor, world.publisher_a)
    fr.calls["render"] = 0
    CHOICES["evaluated"] = 0
    response = _get(client, url, params, modal=modal)
    assert response.status_code == 403
    _assert_not_rendered(fr, response)


@pytest.mark.parametrize("modal", [False, True])
@pytest.mark.django_db
def test_state_disabled_guardian_update_fragment_denied(fr, world, monkeypatch, modal):
    actor = _user("disabled_state")
    _grant(actor, fr.gpub_vs, world.publisher_a, "view", "change")
    seen = []

    def disabled(cls, user, obj=None):
        seen.append(obj)
        return False

    monkeypatch.setattr(fr.GPublisherUpdate, "cv_action_enabled", classmethod(disabled))
    response = _get(
        _client(actor),
        _url(fr.gpub_vs, "update", pk=world.publisher_a.pk),
        {"template": "books", "pk": str(world.publisher_a.pk), "num": "1", "formset_parent_prefix_key": ""},
        modal=modal,
    )
    assert response.status_code == 403
    assert seen == [world.publisher_a]  # the state gate saw the real target
    _assert_not_rendered(fr, response)


@pytest.mark.django_db
def test_missing_guardian_update_target_is_404_before_rendering(fr, world):
    actor = _user("missing_target", superuser=True)
    response = _get(
        _client(actor),
        _url(fr.gpub_vs, "update", pk=987654),
        {"template": "books", "pk": "987654", "num": "1", "formset_parent_prefix_key": ""},
    )
    assert response.status_code == 404
    _assert_not_rendered(fr, response)


@pytest.mark.django_db
def test_wrong_url_parent_guardian_child_fragment_is_404(fr, world):
    """The actor passes the URL-parent gate (publisher A) and holds a grant on book B, but book B is not a child
    of publisher A: the target lookup under the URL parent fails before any rendering."""
    actor = _user("wrong_parent")
    _grant(actor, fr.gpub_vs, world.publisher_a, "view")
    _grant(actor, fr.gbook_vs, world.book_b, "view", "change")
    kwargs = {fr.gbook_vs.parent.get_pk_name(): world.publisher_a.pk, "pk": world.book_b.pk}
    response = _get(
        _client(actor),
        _url(fr.gbook_vs, "update", **kwargs),
        {"template": "notes", "pk": str(world.book_b.pk), "num": "1", "formset_parent_prefix_key": ""},
    )
    assert response.status_code == 404
    _assert_not_rendered(fr, response)


@pytest.mark.django_db
def test_ungranted_guardian_child_update_fragment_denied(fr, world):
    """Parent gate satisfied, no grant on the child row itself."""
    actor = _user("child_ungranted")
    _grant(actor, fr.gpub_vs, world.publisher_a, "view")
    kwargs = {fr.gbook_vs.parent.get_pk_name(): world.publisher_a.pk, "pk": world.book_a.pk}
    response = _get(
        _client(actor),
        _url(fr.gbook_vs, "update", **kwargs),
        {"template": "notes", "pk": str(world.book_a.pk), "num": "1", "formset_parent_prefix_key": ""},
    )
    assert response.status_code == 403
    _assert_not_rendered(fr, response)


# ── preservation: gates that already ran before the fragment ──────────────────


@pytest.mark.parametrize(
    "behavior,status",
    [("redirect", 302), ("403", 403), ("404", 404)],
)
@pytest.mark.django_db
def test_anonymous_fragment_keeps_configured_behavior(fr, world, monkeypatch, behavior, status):
    monkeypatch.setattr(fr.GPublisherUpdate, "cv_guardian_anonymous_behavior", behavior, raising=False)
    response = _get(
        _client(),
        _url(fr.gpub_vs, "update", pk=world.publisher_a.pk),
        {"template": "books", "pk": str(world.publisher_a.pk), "num": "1", "formset_parent_prefix_key": ""},
    )
    assert response.status_code == status
    if status == 302:
        assert "login" in response["Location"]
    _assert_not_rendered(fr, response)


@pytest.mark.django_db
def test_inactive_actor_fragment_keeps_dispatch_403(fr, world):
    actor = _user("inactive_editor")
    _grant(actor, fr.gpub_vs, world.publisher_a, "view", "change")
    actor.is_active = False
    actor.save()
    backends = [ALLOW_INACTIVE, "guardian.backends.ObjectPermissionBackend"]
    with override_settings(AUTHENTICATION_BACKENDS=backends):
        response = _get(
            _client(actor, backend=ALLOW_INACTIVE),
            _url(fr.gpub_vs, "update", pk=world.publisher_a.pk),
            {"template": "books", "pk": str(world.publisher_a.pk), "num": "1", "formset_parent_prefix_key": ""},
        )
    assert response.status_code == 403
    _assert_not_rendered(fr, response)


@pytest.mark.django_db
def test_guardian_top_level_create_fragment_requires_add_permission(fr, world):
    actor = _user("no_add")
    response = _get(
        _client(actor),
        _url(fr.gpub_vs, "create"),
        {"template": "books", "pk": "None", "num": "1", "formset_parent_prefix_key": ""},
    )
    assert response.status_code == 403
    _assert_not_rendered(fr, response)


@pytest.mark.django_db
def test_guardian_child_create_fragment_requires_parent_grant(fr, world):
    actor = _user("no_parent_grant")
    kwargs = {fr.gbook_vs.parent.get_pk_name(): world.publisher_a.pk}
    response = _get(
        _client(actor),
        _url(fr.gbook_vs, "create", **kwargs),
        {"template": "notes", "pk": "None", "num": "1", "formset_parent_prefix_key": ""},
    )
    assert response.status_code == 403
    _assert_not_rendered(fr, response)


@pytest.mark.django_db
def test_guardian_child_create_fragment_state_disabled_and_missing_parent(fr, world, monkeypatch):
    actor = _user("parent_grant")
    _grant(actor, fr.gpub_vs, world.publisher_a, "view")
    client = _client(actor)
    params = {"template": "notes", "pk": "None", "num": "1", "formset_parent_prefix_key": ""}
    pk_name = fr.gbook_vs.parent.get_pk_name()

    missing = _get(client, _url(fr.gbook_vs, "create", **{pk_name: 987654}), params)
    assert missing.status_code == 404

    monkeypatch.setattr(fr.GBookCreate, "cv_action_enabled", classmethod(lambda cls, user, obj=None: False))
    disabled = _get(client, _url(fr.gbook_vs, "create", **{pk_name: world.publisher_a.pk}), params)
    assert disabled.status_code == 403
    _assert_not_rendered(fr, disabled)


@pytest.mark.django_db
def test_core_update_fragment_denied_without_change_or_when_disabled(fr, world, monkeypatch):
    viewer = _user("core_viewer")
    _model_perms(viewer, "view_publisher")
    params = {"template": "books", "pk": str(world.publisher_a.pk), "num": "1", "formset_parent_prefix_key": ""}
    url = _url(fr.cpub_vs, "update", pk=world.publisher_a.pk)
    assert _get(_client(viewer), url, params).status_code == 403

    editor = _user("core_editor")
    _model_perms(editor, "view_publisher", "change_publisher")
    monkeypatch.setattr(fr.CPublisherUpdate, "cv_action_enabled", classmethod(lambda cls, user, obj=None: False))
    response = _get(_client(editor), url, params)
    assert response.status_code == 403
    _assert_not_rendered(fr, response)


# ── authorized browser payload positives (A06), Guardian and core ─────────────


def _guardian_editor(fr, world):
    actor = _user("editor")
    _grant(actor, fr.gpub_vs, world.publisher_a, "view", "change")
    return actor


@pytest.mark.django_db
def test_authorized_guardian_update_fragments_follow_browser_payloads(fr, world):
    pa, ba = world.publisher_a, world.book_a
    client = _client(_guardian_editor(fr, world))
    url = _url(fr.gpub_vs, "update", pk=pa.pk)
    page = client.get(url)
    assert page.status_code == 200
    before = _counts()

    # top-level add-row: one saved book + one extra row rendered -> num=2
    top = browser_add_row(page.content, f"books-{pa.pk}-0")
    assert top == {"template": "books", "pk": str(pa.pk), "num": "2", "formset_parent_prefix_key": ""}
    fragment = _assert_fragment(_get(client, url, top), [f"books-{pa.pk}-0-2"], ["title", "contract"])
    assert SECRET in fragment["html"]  # an authorized editor receives the application's own choices (D-13)

    # nested add-row under the saved book (row 0)
    saved = browser_add_row(page.content, f"books-notes-{pa.pk}-0-0-{ba.pk}-0")
    assert saved == {
        "template": "books|notes",
        "pk": str(ba.pk),
        "num": "1",
        "formset_parent_prefix_key": f"{pa.pk}-0-0",
    }
    _assert_fragment(_get(client, url, saved), [f"books-notes-{pa.pk}-0-0-{ba.pk}-0-1"], ["note", "contract"])

    # nested add-row under the page's unsaved extra row (row 1)
    extra = browser_add_row(page.content, f"books-notes-{pa.pk}-0-1-None-0")
    assert extra == {"template": "books|notes", "pk": "None", "num": "1", "formset_parent_prefix_key": f"{pa.pk}-0-1"}
    _assert_fragment(_get(client, url, extra), [f"books-notes-{pa.pk}-0-1-None-0-1"], ["note"])

    # nested add-row under the client-added book row 2 (above the initial count), from the fragment's metadata
    added = browser_add_row(fragment["html"].encode(), f"books-notes-{pa.pk}-0-2-None-0")
    assert added == {"template": "books|notes", "pk": "None", "num": "1", "formset_parent_prefix_key": f"{pa.pk}-0-2"}
    _assert_fragment(_get(client, url, added), [f"books-notes-{pa.pk}-0-2-None-0-1"], ["note"])

    # the browser may omit the top-level parent prefix entirely
    omitted = {k: v for k, v in top.items() if k != "formset_parent_prefix_key"}
    _assert_fragment(_get(client, url, omitted), [f"books-{pa.pk}-0-2"], ["title"])

    assert _counts() == before


@pytest.mark.django_db
def test_authorized_guardian_create_fragments_follow_browser_payloads(fr, world):
    actor = _user("creator")
    _model_perms(actor, "add_publisher")
    client = _client(actor)
    url = _url(fr.gpub_vs, "create")
    page = client.get(url)
    assert page.status_code == 200
    before = _counts()

    top = browser_add_row(page.content, "books-None-0")
    assert top == {"template": "books", "pk": "None", "num": "1", "formset_parent_prefix_key": ""}
    fragment = _assert_fragment(_get(client, url, top), ["books-None-0-1"], ["title", "contract"])

    nested = browser_add_row(page.content, "books-notes-None-0-0-None-0")
    assert nested == {"template": "books|notes", "pk": "None", "num": "1", "formset_parent_prefix_key": "None-0-0"}
    _assert_fragment(_get(client, url, nested), ["books-notes-None-0-0-None-0-1"], ["note"])

    added = browser_add_row(fragment["html"].encode(), "books-notes-None-0-1-None-0")
    assert added["formset_parent_prefix_key"] == "None-0-1"
    _assert_fragment(_get(client, url, added), ["books-notes-None-0-1-None-0-1"], ["note"])

    omitted = {k: v for k, v in top.items() if k != "formset_parent_prefix_key"}
    _assert_fragment(_get(client, url, omitted), ["books-None-0-1"], ["title"])

    assert _counts() == before


@pytest.mark.django_db
def test_authorized_guardian_child_update_and_create_fragments(fr, world):
    pa, ba = world.publisher_a, world.book_a
    actor = _user("child_editor")
    _grant(actor, fr.gpub_vs, pa, "view")
    _grant(actor, fr.gbook_vs, ba, "view", "change")
    client = _client(actor)
    pk_name = fr.gbook_vs.parent.get_pk_name()
    before = _counts()

    update_url = _url(fr.gbook_vs, "update", **{pk_name: pa.pk, "pk": ba.pk})
    page = client.get(update_url)
    assert page.status_code == 200
    payload = browser_add_row(page.content, f"notes-{ba.pk}-0")
    assert payload == {"template": "notes", "pk": str(ba.pk), "num": "1", "formset_parent_prefix_key": ""}
    _assert_fragment(_get(client, update_url, payload), [f"notes-{ba.pk}-0-1"], ["note"])

    create_url = _url(fr.gbook_vs, "create", **{pk_name: pa.pk})
    page = client.get(create_url)
    assert page.status_code == 200
    payload = browser_add_row(page.content, "notes-None-0")
    _assert_fragment(_get(client, create_url, payload), ["notes-None-0-1"], ["note"])

    assert _counts() == before


@pytest.mark.django_db
def test_authorized_core_update_fragment_follows_browser_payload(fr, world):
    pa = world.publisher_a
    editor = _user("core_editor_ok")
    _model_perms(editor, "view_publisher", "change_publisher")
    client = _client(editor)
    url = _url(fr.cpub_vs, "update", pk=pa.pk)
    page = client.get(url)
    assert page.status_code == 200
    before = _counts()
    payload = browser_add_row(page.content, f"books-{pa.pk}-0")
    _assert_fragment(_get(client, url, payload), [f"books-{pa.pk}-0-2"], ["title"])
    assert _counts() == before


@pytest.mark.django_db
def test_fragment_get_does_not_render_the_full_editor(fr, world, monkeypatch):
    """The fragment branch resolves the target once and returns JSON; it never builds the full page context."""
    pa = world.publisher_a
    client = _client(_guardian_editor(fr, world))
    built = []
    original = fr.GPublisherUpdate.get_context_data

    def spy(self, **kwargs):
        built.append(1)
        return original(self, **kwargs)

    monkeypatch.setattr(fr.GPublisherUpdate, "get_context_data", spy)
    response = _get(
        client,
        _url(fr.gpub_vs, "update", pk=pa.pk),
        {"template": "books", "pk": str(pa.pk), "num": "2", "formset_parent_prefix_key": ""},
    )
    _assert_fragment(response, [f"books-{pa.pk}-0-2"], ["title"])
    assert built == []
    assert fr.calls["render"] == 1


# ── D-12: polymorphic formset composition keeps declaration selection after authorization ──


@pytest.fixture
def poly():
    """Fresh Vehicle routes whose create/update views select formsets per polymorphic model."""
    from crud_views.lib import check as check_module
    from crud_views.lib.crispy import CrispyViewMixin
    from crud_views.lib.formsets.mixins import PolymorphicFormSetsViewMixin
    from crud_views.lib.views import DetailViewPermissionRequired, ListViewPermissionRequired
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet
    from crud_views_polymorphic.lib import (
        PolymorphicCreateViewPermissionRequired,
        PolymorphicUpdateViewPermissionRequired,
    )
    from tests.test1.app.models import Car, Truck, Vehicle
    from tests.test1.app.views import CarForm, TruckForm

    sfx = uuid.uuid4().hex[:8]
    name = f"frveh{sfx}"
    modname = f"tests.test1._fragment_poly_urls_{sfx}"
    vocab_snapshot = dict(check_module._VOCAB_CACHE)
    selected: list = []

    class RecordingSelection:
        def cv_get_formsets(self):
            selected.append((self.polymorphic_model, getattr(self, "object", None)))
            return super().cv_get_formsets()

    try:
        viewset = ViewSet(model=Vehicle, name=name, icon_header="fa-solid fa-car")

        class FrVehicleListView(ListViewPermissionRequired):
            cv_viewset = viewset

        class FrVehicleDetailView(DetailViewPermissionRequired):
            cv_viewset = viewset

        class FrVehicleCreateView(
            RecordingSelection, CrispyViewMixin, PolymorphicFormSetsViewMixin, PolymorphicCreateViewPermissionRequired
        ):
            cv_viewset = viewset
            polymorphic_forms = {Car: CarForm, Truck: TruckForm}
            cv_polymorphic_formsets = {}
            cv_formsets_required = False

        class FrVehicleUpdateView(
            RecordingSelection, CrispyViewMixin, PolymorphicFormSetsViewMixin, PolymorphicUpdateViewPermissionRequired
        ):
            cv_viewset = viewset
            polymorphic_forms = {Car: CarForm, Truck: TruckForm}
            cv_polymorphic_formsets = {}
            cv_formsets_required = False

        module = types.ModuleType(modname)
        module.urlpatterns = [*viewset.urlpatterns, path("", include("tests.test1.project.urls"))]
        sys.modules[modname] = module

        clear_url_caches()
        with override_settings(ROOT_URLCONF=modname):
            clear_url_caches()
            try:
                yield SimpleNamespace(viewset=viewset, selected=selected, Car=Car)
            finally:
                clear_url_caches()
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop(name, None)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocab_snapshot)
        sys.modules.pop(modname, None)
        clear_url_caches()


@pytest.mark.django_db
def test_polymorphic_formset_views_select_declarations_after_authorization(poly):
    from django.contrib.contenttypes.models import ContentType

    car = poly.Car.objects.create(name="Beetle", doors=2)
    editor = _user("poly_editor")
    _model_perms(editor, "view_vehicle", "change_vehicle", "add_vehicle")
    client = _client(editor)
    update_url = _url(poly.viewset, "update", pk=car.pk)
    create_url = _url(poly.viewset, "create", polymorphic_ctype_id=ContentType.objects.get_for_model(poly.Car).id)

    # the full GET/POST paths keep working
    assert client.get(update_url).status_code == 200
    assert client.get(create_url).status_code == 200
    assert client.post(update_url, {"name": "Golf", "doors": "4"}).status_code == 302
    car.refresh_from_db()
    assert car.name == "Golf"
    poly.selected.clear()

    # authorized fragments select the declaration for the resolved model and object; a model without
    # formsets is a 400 (no declaration), never a crash
    params = {"template": "books", "pk": "None", "num": "0", "formset_parent_prefix_key": ""}
    assert _get(client, update_url, params).status_code == 400
    assert _get(client, create_url, params).status_code == 400
    assert [(model, getattr(obj, "pk", None)) for model, obj in poly.selected] == [
        (poly.Car, car.pk),
        (poly.Car, None),
    ]
    poly.selected.clear()

    # an actor who may not edit, and a missing target, are stopped before any declaration lookup
    viewer = _user("poly_viewer")
    _model_perms(viewer, "view_vehicle")
    assert _get(_client(viewer), update_url, params).status_code == 403
    assert _get(client, _url(poly.viewset, "update", pk=987654), params).status_code == 404
    assert poly.selected == []
