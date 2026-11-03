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
from tests.test1.app.models import Author, Book, BookNote, Contract, Publisher, UUIDFragmentLeaf, UUIDFragmentRow

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


def two_child_formsets() -> FormSets:
    """A19: two sibling child declarations under books (notes at index 0, memos at index 1)."""
    return FormSets(
        formsets=OrderedDict(
            books=FormSet(
                title="Books",
                klass=SecretBookFormSet,
                children=OrderedDict(
                    notes=FormSet(title="Notes", klass=SecretNoteFormSet),
                    memos=FormSet(title="Memos", klass=SecretNoteFormSet),
                ),
            )
        )
    )


def three_level_formsets() -> FormSets:
    """Fragment-only declaration three levels deep, so a parent prefix carries a declared child index.

    The leaf declarations reuse the note formset class: fragment rendering never binds them to a row, and the
    ancestry checked for ``books|memos|leaf`` is Publisher -> Book -> BookNote. Only fragment requests use it.
    """
    return FormSets(
        formsets=OrderedDict(
            books=FormSet(
                title="Books",
                klass=SecretBookFormSet,
                children=OrderedDict(
                    notes=FormSet(
                        title="Notes",
                        klass=SecretNoteFormSet,
                        children=OrderedDict(leaf=FormSet(title="Leaf", klass=SecretNoteFormSet)),
                    ),
                    memos=FormSet(
                        title="Memos",
                        klass=SecretNoteFormSet,
                        children=OrderedDict(leaf=FormSet(title="Leaf", klass=SecretNoteFormSet)),
                    ),
                ),
            )
        )
    )


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
    names = [f"frgpub{sfx}", f"frgbook{sfx}", f"frcpub{sfx}", f"frg2pub{sfx}", f"frdeep{sfx}"]
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

        g2pub_vs = GuardianViewSet(model=Publisher, name=names[3], icon_header="fa-regular fa-building")

        class FrG2PublisherListView(GuardianListViewPermissionRequired):
            cv_viewset = g2pub_vs

        class FrG2PublisherDetailView(GuardianDetailViewPermissionRequired):
            cv_viewset = g2pub_vs

        class FrG2PublisherUpdateView(CrispyViewMixin, FormSetMixin, GuardianUpdateViewPermissionRequired):
            form_class = PublisherMainForm
            cv_viewset = g2pub_vs
            cv_formsets = two_child_formsets()

        deep_vs = ViewSet(model=Publisher, name=names[4], icon_header="fa-regular fa-building")

        class FrDeepPublisherListView(ListViewPermissionRequired):
            cv_viewset = deep_vs

        class FrDeepPublisherUpdateView(CrispyViewMixin, FormSetMixin, UpdateViewPermissionRequired):
            form_class = PublisherMainForm
            cv_viewset = deep_vs
            cv_formsets = three_level_formsets()

        module = types.ModuleType(modname)
        module.urlpatterns = [
            *gpub_vs.urlpatterns,
            *gbook_vs.urlpatterns,
            *cpub_vs.urlpatterns,
            *g2pub_vs.urlpatterns,
            *deep_vs.urlpatterns,
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
                    g2pub_vs=g2pub_vs,
                    deep_vs=deep_vs,
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


# ── 03-02: declaration-aware coordinates (integer chains) ─────────────────────


def _editor_client(fr, world, viewset=None):
    actor = _user(f"coord_editor_{uuid.uuid4().hex[:6]}")
    _grant(actor, viewset or fr.gpub_vs, world.publisher_a, "view", "change")
    return _client(actor)


def _assert_bad_request(fr, response, before):
    assert response.status_code == 400, (response.status_code, response.content[:300])
    _assert_not_rendered(fr, response)
    assert _counts() == before


@pytest.mark.parametrize(
    "num",
    ["²", "٣", "1²", "-1", "1.0", "", " 1", "9" * 30, "9" * 5000],
    ids=["superscript", "arabic-indic", "mixed", "negative", "float", "empty", "space", "long", "huge"],
)
@pytest.mark.django_db
def test_malformed_num_is_400_without_rendering(fr, world, num):
    pa = world.publisher_a
    client = _editor_client(fr, world)
    before = _counts()
    response = _get(
        client,
        _url(fr.gpub_vs, "update", pk=pa.pk),
        {"template": "books", "pk": str(pa.pk), "num": num, "formset_parent_prefix_key": ""},
    )
    _assert_bad_request(fr, response, before)


@pytest.mark.parametrize("prefix_tpl", ["{pa}-0-²", "{pa}-²-0", "{pa}-0-٣", "{pa}-0-" + "9" * 5000])
@pytest.mark.django_db
def test_malformed_prefix_index_is_400_without_rendering(fr, world, prefix_tpl):
    pa, ba = world.publisher_a, world.book_a
    client = _editor_client(fr, world)
    before = _counts()
    response = _get(
        client,
        _url(fr.gpub_vs, "update", pk=pa.pk),
        {
            "template": "books|notes",
            "pk": str(ba.pk),
            "num": "1",
            "formset_parent_prefix_key": prefix_tpl.format(pa=pa.pk),
        },
    )
    _assert_bad_request(fr, response, before)


# (template, pk, parent prefix) templates; {pa}/{pb}/{ba}/{bb} are filled from the world fixture.
FORGED_UPDATE = {
    "top-wrong-root": ("books", "{pb}", ""),
    "top-none-root-on-update": ("books", "None", ""),
    "top-nonempty-prefix": ("books", "{pa}", "{pa}-0-0"),
    "top-garbage-prefix": ("books", "{pa}", "x"),
    "top-invalid-identity": ("books", "abc", ""),
    "nested-missing-prefix": ("books|notes", "{ba}", None),
    "nested-empty-prefix": ("books|notes", "{ba}", ""),
    "nested-short-prefix": ("books|notes", "{ba}", "{pa}-0"),
    "nested-long-prefix": ("books|notes", "{ba}", "{pa}-0-0-1"),
    "nested-wrong-root": ("books|notes", "{ba}", "{pb}-0-0"),
    "nested-none-root-on-update": ("books|notes", "None", "None-0-0"),
    "nested-nonzero-top-index": ("books|notes", "{ba}", "{pa}-1-0"),
    "nested-unrelated-ancestor": ("books|notes", "{bb}", "{pa}-0-0"),
    "nested-missing-ancestor": ("books|notes", "987654", "{pa}-0-0"),
    "nested-invalid-identity": ("books|notes", "1e3", "{pa}-0-0"),
    "nested-signed-identity": ("books|notes", "-1", "{pa}-0-0"),
    "nested-uuid-on-int": ("books|notes", str(uuid.UUID(int=1)), "{pa}-0-0"),
    "unknown-key": ("nope", "{pa}", ""),
    "empty-child-key": ("books|", "{ba}", "{pa}-0-0"),
    "empty-root-key": ("|books", "{pa}", ""),
    "child-as-root": ("notes", "{ba}", ""),
    "too-deep-key": ("books|notes|x", "{ba}", "{pa}-0-0"),
}


def _fill(world, value):
    if value is None:
        return None
    return value.format(pa=world.publisher_a.pk, pb=world.publisher_b.pk, ba=world.book_a.pk, bb=world.book_b.pk)


def _coordinate_params(world, template, pk, prefix, num="1"):
    params = {"template": template, "pk": _fill(world, pk), "num": num}
    if prefix is not None:
        params["formset_parent_prefix_key"] = _fill(world, prefix)
    return params


@pytest.mark.parametrize("case", list(FORGED_UPDATE), ids=list(FORGED_UPDATE))
@pytest.mark.django_db
def test_forged_update_coordinates_are_400_without_rendering(fr, world, case):
    client = _editor_client(fr, world)
    before = _counts()
    response = _get(
        client,
        _url(fr.gpub_vs, "update", pk=world.publisher_a.pk),
        _coordinate_params(world, *FORGED_UPDATE[case]),
    )
    _assert_bad_request(fr, response, before)


FORGED_CREATE = {
    "top-saved-root": ("books", "{pa}", ""),
    "nested-saved-root-prefix": ("books|notes", "None", "{pa}-0-0"),
    "nested-saved-under-unsaved": ("books|notes", "{ba}", "None-0-0"),
    "nested-missing-prefix": ("books|notes", "None", None),
}


@pytest.mark.parametrize("case", list(FORGED_CREATE), ids=list(FORGED_CREATE))
@pytest.mark.django_db
def test_forged_create_coordinates_are_400_without_rendering(fr, world, case):
    actor = _user("coord_creator")
    _model_perms(actor, "add_publisher")
    before = _counts()
    response = _get(_client(actor), _url(fr.gpub_vs, "create"), _coordinate_params(world, *FORGED_CREATE[case]))
    _assert_bad_request(fr, response, before)


@pytest.mark.django_db
def test_nested_create_accepts_none_chain_and_new_row_indices(fr, world):
    actor = _user("coord_creator_ok")
    _model_perms(actor, "add_publisher")
    client = _client(actor)
    url = _url(fr.gpub_vs, "create")
    before = _counts()
    for row in ("0", "1", "7", "123456789"):
        response = _get(client, url, _coordinate_params(world, "books|notes", "None", f"None-0-{row}", num="3"))
        _assert_fragment(response, [f"books-notes-None-0-{row}-None-0-3"], ["note"])
    assert _counts() == before


@pytest.mark.django_db
def test_nested_update_accepts_mixed_saved_and_unsaved_chains(fr, world):
    pa, ba = world.publisher_a, world.book_a
    client = _editor_client(fr, world)
    url = _url(fr.gpub_vs, "update", pk=pa.pk)
    before = _counts()
    # saved book at a row index above the initial count (the browser may have reordered or added rows)
    _assert_fragment(
        _get(client, url, _coordinate_params(world, "books|notes", "{ba}", "{pa}-0-5", num="4")),
        [f"books-notes-{pa.pk}-0-5-{ba.pk}-0-4"],
        ["note"],
    )
    # unsaved book rows under the saved publisher, any non-negative index
    for row in ("1", "2", "40"):
        _assert_fragment(
            _get(client, url, _coordinate_params(world, "books|notes", "None", f"{{pa}}-0-{row}")),
            [f"books-notes-{pa.pk}-0-{row}-None-0-1"],
            ["note"],
        )
    assert _counts() == before


@pytest.mark.django_db
def test_parent_ownership_change_applies_on_next_request(fr, world):
    """Fragment GETs are read-only, and each request re-checks persisted ancestry."""
    pa, ba = world.publisher_a, world.book_a
    client = _editor_client(fr, world)
    url = _url(fr.gpub_vs, "update", pk=pa.pk)
    params = _coordinate_params(world, "books|notes", "{ba}", "{pa}-0-0")
    _assert_fragment(_get(client, url, params), [f"books-notes-{pa.pk}-0-0-{ba.pk}-0-1"], ["note"])

    Book.objects.filter(pk=ba.pk).update(publisher=world.publisher_b)
    fr.calls["render"] = 0
    CHOICES["evaluated"] = 0
    _assert_bad_request(fr, _get(client, url, params), _counts())


@pytest.mark.django_db
def test_multi_digit_integer_pks_round_trip_and_truncated_pks_are_rejected(fr, world):
    """Canonical multi-digit ids pass. The truncated ids the old formset.js regex derived ("2" for 12) do not
    match the real ancestry and are rejected instead of rendering rows under a prefix the POST never reads."""
    pub = Publisher.objects.create(id=12, name="Twelve")
    Book.objects.create(id=34, title="Thirty-four", publisher=pub)
    actor = _user("multi_digit")
    _grant(actor, fr.gpub_vs, pub, "view", "change")
    client = _client(actor)
    url = _url(fr.gpub_vs, "update", pk=pub.pk)
    page = client.get(url)
    before = _counts()

    top = browser_add_row(page.content, "books-12-0")
    assert top["pk"] == "12"
    _assert_fragment(_get(client, url, top), ["books-12-0-2"], ["title"])
    nested = browser_add_row(page.content, "books-notes-12-0-0-34-0")
    assert (nested["pk"], nested["formset_parent_prefix_key"]) == ("34", "12-0-0")
    _assert_fragment(_get(client, url, nested), ["books-notes-12-0-0-34-0-1"], ["note"])

    for params in ({**top, "pk": "2"}, {**nested, "pk": "4"}, {**nested, "formset_parent_prefix_key": "2-0-0"}):
        fr.calls["render"] = 0
        CHOICES["evaluated"] = 0
        _assert_bad_request(fr, _get(client, url, params), before)


# ── A19: two sibling child declarations ───────────────────────────────────────


@pytest.mark.django_db
def test_two_child_declaration_characterizes_emitted_index_and_keeps_gates(fr, world):
    """Both siblings keep editor authorization and ancestry validation, and valid ancestor positions pass.

    Known limitation (A19, proposed 6.3, not fixed here): ``FormSet.init`` gives the second sibling index 1,
    while ``FormSets.get_template`` emits index 0 for any selected fragment. The memos fragment's rows therefore
    do not extend the initialized memos formset prefix; this is characterized, not counted as a round trip.
    """
    pa, ba = world.publisher_a, world.book_a
    client = _editor_client(fr, world, viewset=fr.g2pub_vs)
    url = _url(fr.g2pub_vs, "update", pk=pa.pk)
    page = client.get(url)
    assert page.status_code == 200
    meta = _formset_metadata(page.content)
    notes_prefix = f"books-notes-{pa.pk}-0-0-{ba.pk}-0"
    memos_prefix = f"books-memos-{pa.pk}-0-0-{ba.pk}-1"
    assert notes_prefix in meta and memos_prefix in meta
    before = _counts()

    # first child: the fragment extends its initialized formset
    _assert_fragment(_get(client, url, browser_add_row(page.content, notes_prefix)), [f"{notes_prefix}-1"], ["note"])

    memos_payload = browser_add_row(page.content, memos_prefix)
    assert memos_payload == {
        "template": "books|memos",
        "pk": str(ba.pk),
        "num": "1",
        "formset_parent_prefix_key": f"{pa.pk}-0-0",
    }
    memos = _get(client, url, memos_payload).json()
    assert memos["rows"] == [f"books-memos-{pa.pk}-0-0-{ba.pk}-0-1"]  # emitted index 0 ...
    assert not memos["rows"][0].startswith(f"{memos_prefix}-")  # ... not the initialized index 1 (A19)

    for template in ("books|notes", "books|memos"):
        # valid declaration-derived ancestor position: the unsaved extra book row 1
        response = _get(client, url, _coordinate_params(world, template, "None", "{pa}-0-1"))
        assert response.status_code == 200
        # forged ancestry for either sibling
        fr.calls["render"] = 0
        CHOICES["evaluated"] = 0
        forged = _get(client, url, _coordinate_params(world, template, "{bb}", "{pa}-0-0"))
        _assert_bad_request(fr, forged, before)
        # an actor who may not edit gets nothing for either sibling
        denied = _get(
            _client(_user(f"g2_ungranted_{template[-5:]}")),
            url,
            _coordinate_params(world, template, "{ba}", "{pa}-0-0"),
        )
        assert denied.status_code == 403
        _assert_not_rendered(fr, denied)
    assert _counts() == before


# ── declared child positions inside a parent prefix (three levels) ────────────


@pytest.mark.django_db
def test_three_level_prefix_validates_declared_child_index_and_ancestry(fr, world):
    pa, ba, bb = world.publisher_a, world.book_a, world.book_b
    note = BookNote.objects.create(book=ba, note="n-a")
    note_b = BookNote.objects.create(book=bb, note="n-b")
    editor = _user("deep_editor")
    _model_perms(editor, "view_publisher", "change_publisher")
    client = _client(editor)
    url = _url(fr.deep_vs, "update", pk=pa.pk)
    before = _counts()

    # memos is declared at child index 1 under books, notes at 0
    _assert_fragment(
        _get(
            client,
            url,
            {
                "template": "books|memos|leaf",
                "pk": str(note.pk),
                "num": "1",
                "formset_parent_prefix_key": f"{pa.pk}-0-0-{ba.pk}-1-0",
            },
        ),
        [f"books-memos-leaf-{pa.pk}-0-0-{ba.pk}-1-0-{note.pk}-0-1"],
        ["note"],
    )
    _assert_fragment(
        _get(
            client,
            url,
            {
                "template": "books|notes|leaf",
                "pk": "None",
                "num": "2",
                "formset_parent_prefix_key": f"{pa.pk}-0-3-None-0-4",
            },
        ),
        [f"books-notes-leaf-{pa.pk}-0-3-None-0-4-None-0-2"],
        ["note"],
    )

    forged = [
        ("books|memos|leaf", str(note.pk), f"{pa.pk}-0-0-{ba.pk}-0-0"),  # memos is not child 0
        ("books|notes|leaf", str(note.pk), f"{pa.pk}-0-0-{ba.pk}-1-0"),  # notes is not child 1
        ("books|memos|leaf", str(note.pk), f"{pa.pk}-0-0-{ba.pk}-2-0"),  # no child 2
        ("books|memos|leaf", str(note_b.pk), f"{pa.pk}-0-0-{ba.pk}-1-0"),  # note of another book
        ("books|memos|leaf", str(note.pk), f"{pa.pk}-0-0-{bb.pk}-1-0"),  # book of another publisher
        ("books|memos|leaf", str(note.pk), f"{pa.pk}-0-0-None-1-0"),  # saved row under an unsaved one
        ("books|memos|leaf", "None", f"{pa.pk}-0-0-{ba.pk}-1"),  # short
        ("books|memos|leaf", "None", f"{pa.pk}-0-0"),  # parent prefix of the wrong depth
    ]
    for template, pk, prefix in forged:
        response = _get(client, url, {"template": template, "pk": pk, "num": "1", "formset_parent_prefix_key": prefix})
        assert response.status_code == 400, (template, pk, prefix, response.status_code)
    assert _counts() == before


# ── A07/A14: persisted UUID ancestry and unsaved UUID-default rows ────────────


class AuthorMainForm(CrispyModelForm):
    class Meta:
        model = Author
        fields = ["first_name", "last_name"]

    def get_layout_fields(self):
        return [Row(Column4("first_name"), Column4("last_name")), Formsets()]

    @property
    def helper(self):
        h = super().helper
        h.form_tag = False
        return h


class FragmentRowForm(CrispyModelForm):
    class Meta:
        model = UUIDFragmentRow
        fields = ["text"]


class FragmentRowInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        return [Row(Column4("text"), self.form_control_col4)]


class FragmentLeafForm(CrispyModelForm):
    class Meta:
        model = UUIDFragmentLeaf
        fields = ["text"]


class FragmentLeafInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        return [Row(Column4("text"), self.form_control_col4)]


FragmentRowFormSet = inlineformset_factory(
    Author,
    UUIDFragmentRow,
    formset=FragmentRowInlineFormSet,
    form=FragmentRowForm,
    fields=["text"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)

FragmentLeafFormSet = inlineformset_factory(
    UUIDFragmentRow,
    UUIDFragmentLeaf,
    formset=FragmentLeafInlineFormSet,
    form=FragmentLeafForm,
    fields=["text"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)


def author_uuid_formsets() -> FormSets:
    """Root (Author) and nested parent (UUIDFragmentRow) identities both use the UUID grammar."""
    return FormSets(
        formsets=OrderedDict(
            rows=FormSet(
                title="Rows",
                klass=FragmentRowFormSet,
                pk=FormSet.PK.UUID,
                children=OrderedDict(
                    leaves=FormSet(title="Leaves", klass=FragmentLeafFormSet, pk=FormSet.PK.UUID),
                ),
            )
        )
    )


@pytest.fixture
def uu(monkeypatch):
    """Fresh core Author routes with Author -> UUIDFragmentRow -> UUIDFragmentLeaf formsets."""
    from crud_views.lib import check as check_module
    from crud_views.lib.crispy import CrispyViewMixin
    from crud_views.lib.formsets import FormSetMixin
    from crud_views.lib.views import (
        CreateViewPermissionRequired,
        DetailViewPermissionRequired,
        ListViewPermissionRequired,
        UpdateViewPermissionRequired,
    )
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet

    sfx = uuid.uuid4().hex[:8]
    name = f"fruuid{sfx}"
    modname = f"tests.test1._fragment_uuid_urls_{sfx}"
    vocab_snapshot = dict(check_module._VOCAB_CACHE)
    calls = {"render": 0}
    CHOICES["evaluated"] = 0
    original_get_template = FormSets.get_template

    def counting_get_template(self, *args, **kwargs):
        calls["render"] += 1
        return original_get_template(self, *args, **kwargs)

    monkeypatch.setattr(FormSets, "get_template", counting_get_template)

    try:
        viewset = ViewSet(model=Author, name=name, icon_header="fa-regular fa-user")

        class FrAuthorListView(ListViewPermissionRequired):
            cv_viewset = viewset

        class FrAuthorDetailView(DetailViewPermissionRequired):
            cv_viewset = viewset

        class FrAuthorCreateView(CrispyViewMixin, FormSetMixin, CreateViewPermissionRequired):
            form_class = AuthorMainForm
            cv_viewset = viewset
            cv_formsets = author_uuid_formsets()

        class FrAuthorUpdateView(CrispyViewMixin, FormSetMixin, UpdateViewPermissionRequired):
            form_class = AuthorMainForm
            cv_viewset = viewset
            cv_formsets = author_uuid_formsets()

        module = types.ModuleType(modname)
        module.urlpatterns = [*viewset.urlpatterns, path("", include("tests.test1.project.urls"))]
        sys.modules[modname] = module

        clear_url_caches()
        with override_settings(ROOT_URLCONF=modname):
            clear_url_caches()
            try:
                editor = _user(f"uuid_editor_{sfx}")
                _model_perms(editor, "view_author", "add_author", "change_author")
                yield SimpleNamespace(viewset=viewset, calls=calls, client=_client(editor))
            finally:
                clear_url_caches()
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop(name, None)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocab_snapshot)
        sys.modules.pop(modname, None)
        clear_url_caches()


@pytest.fixture
def uworld(db):
    author = Author.objects.create(first_name="Douglas", last_name="Adams")
    other = Author.objects.create(first_name="Terry", last_name="Pratchett")
    row = UUIDFragmentRow.objects.create(author=author, text="row-a")
    leaf = UUIDFragmentLeaf.objects.create(row=row, text="leaf-a")
    other_row = UUIDFragmentRow.objects.create(author=other, text="row-b")
    return SimpleNamespace(author=author, other=other, row=row, leaf=leaf, other_row=other_row)


def _uuid_counts():
    return (Author.objects.count(), UUIDFragmentRow.objects.count(), UUIDFragmentLeaf.objects.count())


def _fragment_inputs(fragment_html: str) -> dict:
    """The submittable inputs of a returned fragment, as a browser would post them once inserted."""
    doc = lxml_html.fragment_fromstring(fragment_html, create_parent="div")
    payload = {}
    for el in doc.cssselect("input, select, textarea"):
        name = el.get("name")
        if not name or (el.get("type") or "").lower() in ("submit", "button", "reset"):
            continue
        if (el.get("type") or "").lower() in ("checkbox", "radio"):
            if el.get("checked") is not None:
                payload[name] = el.get("value", "on")
            continue
        payload[name] = el.text or "" if el.tag == "textarea" else el.get("value") or ""
    return payload


def _assert_uuid_bad_request(uu, response, before):
    assert response.status_code == 400, (response.status_code, response.content[:300])
    assert uu.calls["render"] == 0
    assert _uuid_counts() == before


@pytest.mark.django_db
def test_uuid_saved_chain_fragments_follow_browser_payloads(uu, uworld):
    a, row = uworld.author, uworld.row
    url = _url(uu.viewset, "update", pk=a.pk)
    page = uu.client.get(url)
    assert page.status_code == 200
    before = _uuid_counts()

    top = browser_add_row(page.content, f"rows-{a.pk}-0")
    assert top == {"template": "rows", "pk": str(a.pk), "num": "2", "formset_parent_prefix_key": ""}
    _assert_fragment(uu.client.get(url, top), [f"rows-{a.pk}-0-2"], ["text"])

    saved = browser_add_row(page.content, f"rows-leaves-{a.pk}-0-0-{row.pk}-0")
    assert saved == {
        "template": "rows|leaves",
        "pk": str(row.pk),
        "num": "2",
        "formset_parent_prefix_key": f"{a.pk}-0-0",
    }
    _assert_fragment(uu.client.get(url, saved), [f"rows-leaves-{a.pk}-0-0-{row.pk}-0-2"], ["text"])
    assert _uuid_counts() == before


@pytest.mark.django_db
def test_uuid_forged_ancestry_and_grammar_are_400(uu, uworld):
    a, other, row, other_row = uworld.author, uworld.other, uworld.row, uworld.other_row
    update_url = _url(uu.viewset, "update", pk=a.pk)
    before = _uuid_counts()
    forged = [
        {"template": "rows", "pk": str(other.pk), "num": "1", "formset_parent_prefix_key": ""},
        {"template": "rows", "pk": str(a.pk).upper(), "num": "1", "formset_parent_prefix_key": ""},
        {"template": "rows", "pk": str(a.pk).replace("-", ""), "num": "1", "formset_parent_prefix_key": ""},
        {"template": "rows", "pk": "1", "num": "1", "formset_parent_prefix_key": ""},
        {"template": "rows|leaves", "pk": str(other_row.pk), "num": "1", "formset_parent_prefix_key": f"{a.pk}-0-0"},
        {"template": "rows|leaves", "pk": str(row.pk), "num": "1", "formset_parent_prefix_key": f"{other.pk}-0-0"},
        {"template": "rows|leaves", "pk": str(uuid.uuid4()), "num": "1", "formset_parent_prefix_key": f"{a.pk}-0-0"},
        {"template": "rows|leaves", "pk": str(row.pk), "num": "1", "formset_parent_prefix_key": f"{a.pk}-0"},
        {"template": "rows|leaves", "pk": str(row.pk), "num": "1", "formset_parent_prefix_key": str(a.pk)},
        {"template": "rows|leaves", "pk": str(row.pk), "num": "1"},
    ]
    for params in forged:
        _assert_uuid_bad_request(uu, uu.client.get(update_url, params), before)

    create_url = _url(uu.viewset, "create")
    for params in (
        {"template": "rows", "pk": str(a.pk), "num": "1", "formset_parent_prefix_key": ""},
        {"template": "rows|leaves", "pk": str(row.pk), "num": "1", "formset_parent_prefix_key": "None-0-0"},
        {"template": "rows|leaves", "pk": "None", "num": "1", "formset_parent_prefix_key": f"{a.pk}-0-0"},
    ):
        _assert_uuid_bad_request(uu, uu.client.get(create_url, params), before)


@pytest.mark.django_db
def test_uuid_create_metadata_add_row_and_post_agree(uu, uworld):
    """A14: a new Author already carries a default UUID, but the rendered prefixes use the None sentinel, the
    add-row requests derived from them are accepted, and the bound POST reads the same prefixes."""
    url = _url(uu.viewset, "create")
    page = uu.client.get(url)
    assert page.status_code == 200
    meta = _formset_metadata(page.content)
    assert "rows-None-0" in meta
    assert "rows-leaves-None-0-0-None-0" in meta

    top = browser_add_row(page.content, "rows-None-0")
    assert top == {"template": "rows", "pk": "None", "num": "1", "formset_parent_prefix_key": ""}
    fragment = _assert_fragment(uu.client.get(url, top), ["rows-None-0-1"], ["text"])
    nested = browser_add_row(fragment["html"].encode(), "rows-leaves-None-0-1-None-0")
    assert nested == {"template": "rows|leaves", "pk": "None", "num": "1", "formset_parent_prefix_key": "None-0-1"}
    _assert_fragment(uu.client.get(url, nested), ["rows-leaves-None-0-1-None-0-1"], ["text"])

    from tests.lib.helper.forms import form_payload

    payload = {**form_payload(page), **_fragment_inputs(fragment["html"])}
    payload["rows-None-0-TOTAL_FORMS"] = "2"
    payload.update(
        {
            "first_name": "Ursula",
            "last_name": "Le Guin",
            "rows-None-0-0-text": "row-0",
            "rows-leaves-None-0-0-None-0-0-text": "leaf-0",
            "rows-None-0-1-text": "row-1",
            "rows-leaves-None-0-1-None-0-0-text": "leaf-1",
        }
    )
    response = uu.client.post(url, payload)
    assert response.status_code == 302, response.content[:2000]

    created = Author.objects.get(first_name="Ursula")
    rows = {r.text: r for r in created.fragment_rows.all()}
    assert set(rows) == {"row-0", "row-1"}
    assert all(isinstance(r.pk, uuid.UUID) for r in rows.values())  # real UUIDs were kept, never cleared
    assert list(rows["row-0"].leaves.values_list("text", flat=True)) == ["leaf-0"]
    assert list(rows["row-1"].leaves.values_list("text", flat=True)) == ["leaf-1"]


@pytest.mark.django_db
def test_uuid_update_extra_rows_render_none_and_post_binds(uu, uworld):
    a, row = uworld.author, uworld.row
    url = _url(uu.viewset, "update", pk=a.pk)
    page = uu.client.get(url)
    meta = _formset_metadata(page.content)
    assert f"rows-leaves-{a.pk}-0-0-{row.pk}-0" in meta  # the saved row keeps its real UUID
    assert f"rows-leaves-{a.pk}-0-1-None-0" in meta  # the extra row's default UUID is not a coordinate

    from tests.lib.helper.forms import form_payload

    payload = form_payload(page)
    assert payload[f"rows-{a.pk}-0-0-id"] == str(row.pk)

    extra = browser_add_row(page.content, f"rows-leaves-{a.pk}-0-1-None-0")
    assert extra == {"template": "rows|leaves", "pk": "None", "num": "1", "formset_parent_prefix_key": f"{a.pk}-0-1"}
    _assert_fragment(uu.client.get(url, extra), [f"rows-leaves-{a.pk}-0-1-None-0-1"], ["text"])

    top = browser_add_row(page.content, f"rows-{a.pk}-0")
    fragment = _assert_fragment(uu.client.get(url, top), [f"rows-{a.pk}-0-2"], ["text"])

    payload.update(_fragment_inputs(fragment["html"]))
    payload[f"rows-{a.pk}-0-TOTAL_FORMS"] = "3"
    payload.update(
        {
            f"rows-{a.pk}-0-1-text": "row-extra",
            f"rows-leaves-{a.pk}-0-1-None-0-0-text": "leaf-extra",
            f"rows-{a.pk}-0-2-text": "row-added",
            f"rows-leaves-{a.pk}-0-2-None-0-0-text": "leaf-added",
        }
    )
    response = uu.client.post(url, payload)
    assert response.status_code == 302, response.content[:2000]

    texts = {r.text: list(r.leaves.values_list("text", flat=True)) for r in a.fragment_rows.all()}
    assert texts == {"row-a": ["leaf-a"], "row-extra": ["leaf-extra"], "row-added": ["leaf-added"]}
    row.refresh_from_db()
    assert row.author_id == a.pk
