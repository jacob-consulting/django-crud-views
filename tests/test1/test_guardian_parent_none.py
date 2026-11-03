"""Phase 6.2 B4/B6 (AUTH-04): parent-permission-free creation with real parent/state enforcement.

``cv_guardian_parent_permission = None`` (and a create permission falling back to it) disables only the parent
*permission* evaluation. The URL parent is still resolved (missing parents 404) and the independent no-object action
state is still evaluated with that parent. Create helpers and direct GET/POST agree, without a child-add grant.

Every route here is built by a yielding fixture on fresh, uniquely named ViewSets with a temporary ROOT_URLCONF;
the registry, vocabulary cache, URL caches and module registration are restored in ``finally`` (A08).
"""

import sys
import types
import uuid
from types import SimpleNamespace

import pytest
from django.http import Http404
from django.test import override_settings
from django.urls import clear_url_caches, include, path, reverse

from tests.lib.helper.guardian import user_guardian_object_perm

# ── isolated route fixture ────────────────────────────────────────────────────


@pytest.fixture
def pn():
    """Fresh nested Guardian routes: Publisher parent, None-policy Book child (FK), Genre child (M2M) and a
    composition child whose views inherit custom global/anonymous policies through the parent mixin."""
    from crud_views.lib import check as check_module
    from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
    from crud_views.lib.view import CardAction, ContextButton
    from crud_views.lib.views import CreateViewParentMixin, DetailViewPermissionRequired, ListViewPermissionRequired
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ParentViewSet, context_buttons_default
    from crud_views_guardian.lib.mixins import (
        GuardianObjectPermissionMixin,
        GuardianParentPermissionMixin,
        GuardianQuerysetMixin,
    )
    from crud_views_guardian.lib.views import (
        GuardianCardListViewPermissionRequired,
        GuardianCreateViewPermissionRequired,
        GuardianDeleteViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
        GuardianUpdateViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Book, Genre, Publisher
    from tests.test1.app.views import BookForm, GenreForm

    sfx = uuid.uuid4().hex[:8]
    names = [f"pnpub{sfx}", f"pnbook{sfx}", f"pngenre{sfx}", f"pncomp{sfx}"]
    vocab_snapshot = dict(check_module._VOCAB_CACHE)
    modname = f"tests.test1._pn_urls_{sfx}"
    state = {"enabled": True}
    hook_calls: list = []

    try:
        pub_vs = GuardianViewSet(model=Publisher, name=names[0], icon_header="fa-regular fa-building")

        class PnPublisherListView(GuardianListViewPermissionRequired):
            cv_viewset = pub_vs

        class PnPublisherDetailView(GuardianDetailViewPermissionRequired):
            cv_viewset = pub_vs

        class PnPublisherCardView(GuardianCardListViewPermissionRequired):
            cv_viewset = pub_vs
            # child branch of a card action: the row (a Publisher) is the create target's parent
            cv_card_actions = [CardAction(child_name=names[1], child_key="create", label="Add book")]

        book_vs = GuardianViewSet(
            model=Book,
            name=names[1],
            parent=ParentViewSet(name=names[0], attribute="publisher"),
            icon_header="fa-regular fa-address-book",
            cv_guardian_parent_permission=None,
            cv_guardian_parent_create_permission=None,
            context_buttons=[
                *context_buttons_default(),
                ContextButton(key="create_alias", key_target="create", label_template_code="Another book"),
            ],
        )
        child_page_actions = ["home", "create", "create_alias"]

        class PnBookListView(GuardianListViewPermissionRequired):
            cv_viewset = book_vs
            cv_context_actions = ["parent", "create"]

        class PnBookDetailView(GuardianDetailViewPermissionRequired):
            cv_viewset = book_vs
            cv_context_actions = child_page_actions

        class PnBookUpdateView(CrispyViewMixin, GuardianUpdateViewPermissionRequired):
            form_class = BookForm
            cv_viewset = book_vs
            cv_context_actions = child_page_actions

        class PnBookDeleteView(CrispyViewMixin, GuardianDeleteViewPermissionRequired):
            form_class = CrispyDeleteForm
            cv_viewset = book_vs
            cv_context_actions = child_page_actions

        class PnBookCardView(GuardianCardListViewPermissionRequired):
            cv_viewset = book_vs
            cv_context_actions = ["create"]
            # key branch of a card action: the row (a Book) is an own child of the create target
            cv_card_actions = [CardAction(key="create", label="Sibling book"), CardAction(key="detail", label="Open")]

        class PnBookCreateView(CrispyViewMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired):
            form_class = BookForm
            cv_viewset = book_vs

            @classmethod
            def cv_action_enabled(cls, user, obj=None):
                hook_calls.append(obj)
                return state["enabled"]

        genre_vs = GuardianViewSet(
            model=Genre,
            name=names[2],
            parent=ParentViewSet(name=names[0], attribute="publishers", many_to_many_through_attribute="genres"),
            icon_header="fa-solid fa-tag",
            cv_guardian_parent_permission="view",
            cv_guardian_parent_create_permission="change",
        )

        class PnGenreListView(GuardianListViewPermissionRequired):
            cv_viewset = genre_vs
            cv_context_actions = ["create"]

        class PnGenreCreateView(CrispyViewMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired):
            form_class = GenreForm
            cv_viewset = genre_vs

            @classmethod
            def cv_action_enabled(cls, user, obj=None):
                hook_calls.append(obj)
                return state["enabled"]

        # custom object/queryset mixins carrying non-default policies, composed AFTER the parent mixin (A23)
        class CustomObjectMixin(GuardianObjectPermissionMixin):
            cv_guardian_accept_global_perms = True
            cv_guardian_anonymous_behavior = "404"

        class CustomQuerysetMixin(GuardianQuerysetMixin):
            cv_guardian_accept_global_perms = True
            cv_guardian_anonymous_behavior = "404"

        comp_vs = GuardianViewSet(
            model=Book,
            name=names[3],
            parent=ParentViewSet(name=names[0], attribute="publisher"),
            icon_header="fa-regular fa-address-book",
        )

        class PnCompListView(GuardianParentPermissionMixin, CustomQuerysetMixin, ListViewPermissionRequired):
            cv_viewset = comp_vs

        class PnCompDetailView(GuardianParentPermissionMixin, CustomObjectMixin, DetailViewPermissionRequired):
            cv_viewset = comp_vs

        module = types.ModuleType(modname)
        module.urlpatterns = [
            *pub_vs.urlpatterns,
            *book_vs.urlpatterns,
            *genre_vs.urlpatterns,
            *comp_vs.urlpatterns,
            path("", include("tests.test1.project.urls")),
        ]
        sys.modules[modname] = module

        clear_url_caches()
        with override_settings(ROOT_URLCONF=modname):
            clear_url_caches()
            try:
                yield SimpleNamespace(
                    pub_vs=pub_vs,
                    book_vs=book_vs,
                    genre_vs=genre_vs,
                    comp_vs=comp_vs,
                    PublisherDetail=PnPublisherDetailView,
                    PublisherCard=PnPublisherCardView,
                    BookList=PnBookListView,
                    BookDetail=PnBookDetailView,
                    BookUpdate=PnBookUpdateView,
                    BookDelete=PnBookDeleteView,
                    BookCard=PnBookCardView,
                    BookCreate=PnBookCreateView,
                    GenreList=PnGenreListView,
                    GenreCreate=PnGenreCreateView,
                    CompList=PnCompListView,
                    CompDetail=PnCompDetailView,
                    state=state,
                    hook_calls=hook_calls,
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


def _url(viewset, key, parent_pk, pk=None):
    kwargs = {viewset.parent.get_pk_name(): parent_pk}
    if pk is not None:
        kwargs["pk"] = pk
    return reverse(viewset.get_router_name(key), kwargs=kwargs)


def _user(username, *, superuser=False, active=True):
    from django.contrib.auth.models import User

    if superuser:
        user = User.objects.create_superuser(username=username, password="password")
    else:
        user = User.objects.create_user(username=username, password="password")
    if not active:
        user.is_active = False
        user.save()
    return user


def _grant_global(user, *codenames):
    from django.contrib.auth.models import Permission, User

    for codename in codenames:
        user.user_permissions.add(Permission.objects.get(codename=codename))
    return User.objects.get(pk=user.pk)  # drop Django's per-instance permission cache


def _record_contexts(monkeypatch, view_cls):
    """Wrap view_cls.cv_get_context, recording (key, resolved context) for every call."""
    records: list = []
    original = view_cls.cv_get_context

    def spy(self, *args, **kwargs):
        ctx = original(self, *args, **kwargs)
        records.append((kwargs.get("key"), ctx))
        return ctx

    monkeypatch.setattr(view_cls, "cv_get_context", spy)
    return records


def _create_contexts(records):
    return [ctx for key, ctx in records if key == "create"]


# ── enabled / disabled / missing parent under the None policy (D-10, A10) ─────


@pytest.mark.django_db
def test_none_policy_enabled_create_get_200_post_302_binds_url_parent(pn, client, publisher_a):
    from tests.test1.app.models import Book, Publisher

    client.force_login(_user("no_grants"))
    url = _url(pn.book_vs, "create", publisher_a.pk)

    assert client.get(url).status_code == 200
    response = client.post(url, {"title": "Parentless Policy"})
    assert response.status_code == 302

    books = list(Book.objects.filter(title="Parentless Policy"))
    assert len(books) == 1
    assert books[0].publisher_id == publisher_a.pk
    # the independent state gate ran with the URL parent on both requests — never with None or a Book
    assert pn.hook_calls
    assert all(isinstance(obj, Publisher) and obj.pk == publisher_a.pk for obj in pn.hook_calls)


@pytest.mark.django_db
def test_none_policy_disabled_create_get_post_403_without_write(pn, client, publisher_a):
    from tests.test1.app.models import Book

    pn.state["enabled"] = False
    client.force_login(_user("no_grants"))
    url = _url(pn.book_vs, "create", publisher_a.pk)

    assert client.get(url).status_code == 403
    assert client.post(url, {"title": "Disabled Parent"}).status_code == 403
    assert not Book.objects.filter(title="Disabled Parent").exists()


@pytest.mark.django_db
def test_none_policy_missing_parent_create_404_without_write(pn, client):
    from tests.test1.app.models import Book

    client.force_login(_user("no_grants"))
    url = _url(pn.book_vs, "create", 999999)

    assert client.get(url).status_code == 404
    assert client.post(url, {"title": "Orphan"}).status_code == 404
    assert not Book.objects.filter(title="Orphan").exists()
    assert pn.hook_calls == []


@pytest.mark.django_db
def test_none_policy_missing_parent_list_404_at_dispatch(pn, client):
    client.force_login(_user("no_grants"))
    assert client.get(_url(pn.book_vs, "list", 999999)).status_code == 404
    assert pn.hook_calls == []


@pytest.mark.django_db
def test_none_policy_forged_fk_post_binds_url_parent(pn, client, publisher_a, publisher_b):
    from tests.test1.app.models import Book

    client.force_login(_user("no_grants"))
    url = _url(pn.book_vs, "create", publisher_a.pk)
    response = client.post(url, {"title": "Forged", "publisher": publisher_b.pk})
    assert response.status_code == 302
    assert list(Book.objects.filter(title="Forged").values_list("publisher_id", flat=True)) == [publisher_a.pk]


@pytest.mark.django_db
def test_none_policy_interleaved_parents_bind_each_request_to_its_url_parent(pn, client, publisher_a, publisher_b):
    """Edge AUTH-04 concurrency: each request resolves its own parent; no cached authority is shared."""
    from tests.test1.app.models import Book

    client.force_login(_user("no_grants"))
    for title, parent in [("A1", publisher_a), ("B1", publisher_b), ("A2", publisher_a)]:
        assert client.post(_url(pn.book_vs, "create", parent.pk), {"title": title}).status_code == 302

    assert dict(Book.objects.filter(title__in=["A1", "B1", "A2"]).values_list("title", "publisher_id")) == {
        "A1": publisher_a.pk,
        "B1": publisher_b.pk,
        "A2": publisher_a.pk,
    }
    assert [obj.pk for obj in pn.hook_calls] == [publisher_a.pk, publisher_b.pk, publisher_a.pk]

    # disabling only parent B is honoured on the next request, A keeps working
    pn.state["enabled"] = True
    original = pn.BookCreate.cv_action_enabled.__func__

    @classmethod
    def per_parent(cls, user, obj=None):
        original(cls, user, obj)
        return obj is not None and obj.pk != publisher_b.pk

    pn.BookCreate.cv_action_enabled = per_parent
    try:
        assert client.post(_url(pn.book_vs, "create", publisher_b.pk), {"title": "B2"}).status_code == 403
        assert client.post(_url(pn.book_vs, "create", publisher_a.pk), {"title": "A3"}).status_code == 302
    finally:
        del pn.BookCreate.cv_action_enabled
        pn.BookCreate.cv_action_enabled = classmethod(original)
    assert not Book.objects.filter(title="B2").exists()
    assert Book.objects.get(title="A3").publisher_id == publisher_a.pk


# ── helpers under the None policy agree with direct requests (B6) ─────────────


@pytest.mark.django_db
def test_none_policy_helpers_allow_parent_and_own_child_without_grants(pn, publisher_a):
    from tests.test1.app.models import Book

    user = _user("no_grants")
    book = Book.objects.create(title="Own child", publisher=publisher_a)

    assert pn.BookCreate.cv_has_access(user, publisher_a) is True
    assert pn.BookCreate.cv_create_has_access(user, None, publisher_a) is True
    assert pn.BookCreate.cv_has_access(user, book) is True
    assert pn.BookCreate.cv_create_has_access(user, None, book) is True


@pytest.mark.django_db
def test_none_policy_helpers_deny_none_and_unrelated_inputs(pn, author_douglas_adams):
    from tests.test1.app.models import Book

    for user in (_user("no_grants"), _user("root", superuser=True)):
        assert pn.BookCreate.cv_has_access(user, None) is False
        assert pn.BookCreate.cv_create_has_access(user, None, None) is False
        assert pn.BookCreate.cv_has_access(user, author_douglas_adams) is False
        assert pn.BookCreate.cv_create_has_access(user, None, author_douglas_adams) is False
        # an unsaved child without its parent relation cannot establish a parent
        assert pn.BookCreate.cv_has_access(user, Book(title="no parent")) is False
    assert pn.hook_calls == []


@pytest.mark.django_db
def test_none_policy_helper_evaluation_is_side_effect_free(pn, client, publisher_a):
    """Edge AUTH-04 idempotency: repeated helper/context evaluation cannot change request authorization."""
    from tests.test1.app.models import Book

    user = _user("no_grants")
    for _ in range(3):
        assert pn.BookCreate.cv_has_access(user, publisher_a) is True
        assert pn.BookCreate.cv_create_has_access(user, None, publisher_a) is True
        assert pn.BookCreate._cv_action_enabled_for_context(user, publisher_a) is True

    pn.state["enabled"] = False
    client.force_login(user)
    url = _url(pn.book_vs, "create", publisher_a.pk)
    assert client.get(url).status_code == 403
    assert client.post(url, {"title": "Still disabled"}).status_code == 403
    assert not Book.objects.filter(title="Still disabled").exists()


# ── list create control: real parent success and late fallback failure (A24) ──


@pytest.mark.django_db
def test_list_create_control_uses_url_parent_for_state(pn, client, monkeypatch, publisher_a):
    from tests.test1.app.models import Publisher

    records = _record_contexts(monkeypatch, pn.BookList)
    client.force_login(_user("no_grants"))
    url = _url(pn.book_vs, "list", publisher_a.pk)
    create_url = _url(pn.book_vs, "create", publisher_a.pk)

    response = client.get(url)
    assert response.status_code == 200
    (ctx,) = _create_contexts(records)
    assert ctx["cv_access"] is True
    assert ctx["cv_action_enabled"] is True
    assert create_url in response.content.decode()
    assert pn.hook_calls and all(isinstance(obj, Publisher) for obj in pn.hook_calls)

    # authorized but state-disabled: permission field stays True, state False, button unavailable
    records.clear()
    pn.state["enabled"] = False
    response = client.get(url)
    assert response.status_code == 200
    (ctx,) = _create_contexts(records)
    assert ctx["cv_access"] is True
    assert ctx["cv_action_enabled"] is False
    assert f'href="{create_url}"' not in response.content.decode()
    assert all(isinstance(obj, Publisher) for obj in pn.hook_calls)


@pytest.mark.parametrize("error", [Http404, KeyError])
@pytest.mark.django_db
def test_list_create_control_late_parent_failure_skips_state_hook(pn, client, monkeypatch, publisher_a, error):
    """Dispatch resolves the parent; only the later cv_get_parent_object fallback fails."""
    from tests.test1.app.models import Book

    def fail(self):
        raise error("late failure")

    monkeypatch.setattr(pn.BookList, "cv_get_parent_object", fail)
    records = _record_contexts(monkeypatch, pn.BookList)
    client.force_login(_user("no_grants"))
    before = Book.objects.count()

    response = client.get(_url(pn.book_vs, "list", publisher_a.pk))
    assert response.status_code == 200
    (ctx,) = _create_contexts(records)
    assert ctx["cv_access"] is False
    assert ctx["cv_action_enabled"] is False
    assert None not in pn.hook_calls
    assert Book.objects.count() == before


# ── parent-mixin configuration annotations (A13/A23) ─────────────────────────


def test_parent_mixin_declares_policy_names_without_values():
    from crud_views_guardian.lib.mixins import GuardianParentPermissionMixin

    annotations = GuardianParentPermissionMixin.__annotations__
    assert "cv_guardian_accept_global_perms" in annotations
    assert "cv_guardian_anonymous_behavior" in annotations
    # annotation-only: no values that could shadow a later object/queryset mixin's policy
    assert "cv_guardian_accept_global_perms" not in vars(GuardianParentPermissionMixin)
    assert "cv_guardian_anonymous_behavior" not in vars(GuardianParentPermissionMixin)


def test_parent_only_view_policy_settings_raise_no_w280(monkeypatch):
    """A parent-mixin-only view (Guardian create) may set both policies; the names are known from its own MRO."""
    from crud_views.lib import check as check_module
    from crud_views.lib.check import CheckUnknownAttributes
    from crud_views_guardian.lib.views import GuardianCreateViewPermissionRequired

    # isolate from the package-wide registry so only this view's own MRO defines the known-set
    monkeypatch.setattr(check_module, "_registry_vocabulary", lambda: (frozenset(), frozenset()))

    class ExplicitPolicyCreate(GuardianCreateViewPermissionRequired):  # unregistered: no cv_viewset in body
        cv_guardian_accept_global_perms = True
        cv_guardian_anonymous_behavior = "404"

    class TypoPolicyCreate(GuardianCreateViewPermissionRequired):
        cv_guardian_acept_global_perms = True

    assert list(CheckUnknownAttributes(context=ExplicitPolicyCreate).messages()) == []
    typo = list(CheckUnknownAttributes(context=TypoPolicyCreate).messages())
    assert [m.id for m in typo] == ["viewset.W280"]
    assert "cv_guardian_accept_global_perms" in typo[0].msg


@pytest.mark.django_db
def test_composed_custom_policies_stay_inherited_through_parent_mixin(pn, client, publisher_a):
    from tests.test1.app.models import Book

    for cls in (pn.CompList, pn.CompDetail):
        assert cls.cv_guardian_accept_global_perms is True
        assert cls.cv_guardian_anonymous_behavior == "404"

    book = Book.objects.create(title="Global Only", publisher=publisher_a)
    list_url = _url(pn.comp_vs, "list", publisher_a.pk)
    detail_url = _url(pn.comp_vs, "detail", publisher_a.pk, book.pk)

    # anonymous → 404 (the custom mixins' policy), not the login redirect
    assert client.get(list_url).status_code == 404
    assert client.get(detail_url).status_code == 404

    # global-only permissions satisfy parent, queryset and object checks via the inherited fallback
    user = _grant_global(_user("global_only"), "view_publisher", "view_book")
    client.force_login(user)
    response = client.get(list_url)
    assert response.status_code == 200
    assert "Global Only" in response.content.decode()
    assert client.get(detail_url).status_code == 200

    # without any permission the inherited fallback still denies
    client.force_login(_user("nobody"))
    assert client.get(list_url).status_code == 403
    assert client.get(detail_url).status_code == 403


# ── M2M own-child boundary (A25) ──────────────────────────────────────────────


@pytest.fixture
def genre_two_parents(publisher_a, publisher_b):
    from tests.test1.app.models import Genre

    genre = Genre.objects.create(name="Shared")
    genre.publishers.add(publisher_a, publisher_b)
    return genre


@pytest.mark.parametrize("none_policy", [False, True])
@pytest.mark.django_db
def test_m2m_own_child_inputs_deny_without_state_hook(pn, monkeypatch, genre_two_parents, publisher_a, none_policy):
    if none_policy:
        monkeypatch.setattr(pn.genre_vs, "cv_guardian_parent_permission", None)
        monkeypatch.setattr(pn.genre_vs, "cv_guardian_parent_create_permission", None)
    user = _user("granted")
    user_guardian_object_perm(user, pn.pub_vs, "change", publisher_a)

    for actor in (user, _user("root", superuser=True)):
        assert pn.GenreCreate.cv_has_access(actor, genre_two_parents) is False
        assert pn.GenreCreate.cv_create_has_access(actor, None, genre_two_parents) is False
        assert pn.GenreCreate._cv_action_enabled_for_context(actor, genre_two_parents) is False
    assert pn.hook_calls == []


@pytest.mark.django_db
def test_m2m_explicit_parent_helpers_keep_permission_results(pn, monkeypatch, publisher_a, publisher_b):
    user = _user("granted")
    user_guardian_object_perm(user, pn.pub_vs, "change", publisher_a)

    assert pn.GenreCreate.cv_has_access(user, publisher_a) is True
    assert pn.GenreCreate.cv_create_has_access(user, None, publisher_a) is True
    assert pn.GenreCreate.cv_has_access(user, publisher_b) is False
    assert pn.GenreCreate.cv_create_has_access(user, None, publisher_b) is False

    monkeypatch.setattr(pn.genre_vs, "cv_guardian_parent_permission", None)
    monkeypatch.setattr(pn.genre_vs, "cv_guardian_parent_create_permission", None)
    assert pn.GenreCreate.cv_has_access(user, publisher_b) is True
    assert pn.GenreCreate.cv_create_has_access(user, None, publisher_b) is True


@pytest.mark.django_db
def test_m2m_url_bound_list_and_create_link_only_url_parent(pn, client, monkeypatch, publisher_a, publisher_b):
    from tests.test1.app.models import Genre, Publisher

    user = _user("granted")
    user_guardian_object_perm(user, pn.pub_vs, "view", publisher_a)
    user_guardian_object_perm(user, pn.pub_vs, "change", publisher_a)
    client.force_login(user)

    records = _record_contexts(monkeypatch, pn.GenreList)
    assert client.get(_url(pn.genre_vs, "list", publisher_a.pk)).status_code == 200
    (ctx,) = _create_contexts(records)
    assert ctx["cv_access"] is True
    assert ctx["cv_action_enabled"] is True

    url = _url(pn.genre_vs, "create", publisher_a.pk)
    assert client.get(url).status_code == 200
    assert client.post(url, {"name": "Linked"}).status_code == 302
    genre = Genre.objects.get(name="Linked")
    assert list(genre.publishers.values_list("pk", flat=True)) == [publisher_a.pk]
    assert all(isinstance(obj, Publisher) and obj.pk == publisher_a.pk for obj in pn.hook_calls)

    # the other parent stays denied for this actor
    assert client.post(_url(pn.genre_vs, "create", publisher_b.pk), {"name": "Denied"}).status_code == 403
    assert not Genre.objects.filter(name="Denied").exists()


@pytest.mark.django_db
def test_m2m_none_policy_create_without_grants(pn, client, monkeypatch, publisher_a, publisher_b):
    from tests.test1.app.models import Genre

    monkeypatch.setattr(pn.genre_vs, "cv_guardian_parent_permission", None)
    monkeypatch.setattr(pn.genre_vs, "cv_guardian_parent_create_permission", None)
    client.force_login(_user("no_grants"))

    url = _url(pn.genre_vs, "create", publisher_b.pk)
    assert client.get(url).status_code == 200
    assert client.post(url, {"name": "Free"}).status_code == 302
    assert list(Genre.objects.get(name="Free").publishers.values_list("pk", flat=True)) == [publisher_b.pk]

    pn.state["enabled"] = False
    assert client.get(url).status_code == 403
    assert client.post(url, {"name": "Blocked"}).status_code == 403
    assert not Genre.objects.filter(name="Blocked").exists()
    assert not publisher_b.genres.filter(name="Blocked").exists()


# ── inactive actors under the None policy (D-11) ─────────────────────────────


@pytest.mark.parametrize("superuser", [False, True])
@pytest.mark.django_db
def test_none_policy_inactive_actor_denied_create_and_list(pn, client, publisher_a, superuser):
    """A None parent policy skips the permission check, never the inactive-actor denial."""
    from tests.test1.app.models import Book

    backend = "django.contrib.auth.backends.AllowAllUsersModelBackend"
    user = _user("inactive", superuser=superuser, active=False)
    Book.objects.create(title="Listed Row", publisher=publisher_a)
    with override_settings(AUTHENTICATION_BACKENDS=[backend, "guardian.backends.ObjectPermissionBackend"]):
        client.force_login(user, backend=backend)
        url = _url(pn.book_vs, "create", publisher_a.pk)
        assert client.get(url).status_code == 403
        assert client.post(url, {"title": "Inactive None"}).status_code == 403
        response = client.get(_url(pn.book_vs, "list", publisher_a.pk))
        assert response.status_code == 403
        assert "Listed Row" not in response.content.decode()
    assert not Book.objects.filter(title="Inactive None").exists()
    assert pn.BookCreate.cv_has_access(user, publisher_a) is False
    assert pn.BookCreate.cv_create_has_access(user, None, publisher_a) is False


# ── child-page and card create controls use the real parent (H03, D-10/D-12) ──


def _strict_policy(pn, monkeypatch):
    """Book child pages need parent 'view'; creating a Book needs parent 'change'."""
    monkeypatch.setattr(pn.book_vs, "cv_guardian_parent_permission", "view")
    monkeypatch.setattr(pn.book_vs, "cv_guardian_parent_create_permission", "change")


def _child_page_actor(pn, publisher, book, *, create_grant, name="child_page"):
    """May open the Book's detail/update/delete pages (parent view + own object grants), independently of the
    parent create grant."""
    user = _user(name)
    user_guardian_object_perm(user, pn.pub_vs, "view", publisher)
    for perm in ("view", "change", "delete"):
        user_guardian_object_perm(user, pn.book_vs, perm, book)
    if create_grant:
        user_guardian_object_perm(user, pn.pub_vs, "change", publisher)
    return user


def _assert_hook_saw_only_parent(pn, publisher):
    from tests.test1.app.models import Publisher

    assert pn.hook_calls, "the create state hook was not consulted"
    assert all(type(obj) is Publisher and obj.pk == publisher.pk for obj in pn.hook_calls), pn.hook_calls


def _render_filter_and_button(response):
    from django.template import Context, Template

    view = response.context["view"]
    template = Template(
        '{% load crud_views %}{{ view|cv_context_has_permission:"create" }}|{% cv_context_button "create" %}'
    )
    permission, button = template.render(Context({"view": view, "request": view.request})).split("|", 1)
    return permission, button


PAGES = ["detail", "update", "delete"]


@pytest.fixture
def child(pn, publisher_a):
    from tests.test1.app.models import Book

    return Book.objects.create(title="Child Page Book", publisher=publisher_a)


@pytest.mark.parametrize("page", PAGES)
@pytest.mark.parametrize("create_grant", [True, False])
@pytest.mark.django_db
def test_child_page_create_controls_follow_parent_grant(
    pn, client, monkeypatch, publisher_a, child, page, create_grant
):
    _strict_policy(pn, monkeypatch)
    page_cls = {"detail": pn.BookDetail, "update": pn.BookUpdate, "delete": pn.BookDelete}[page]
    records = _record_contexts(monkeypatch, page_cls)
    client.force_login(_child_page_actor(pn, publisher_a, child, create_grant=create_grant))
    create_url = _url(pn.book_vs, "create", publisher_a.pk)

    response = client.get(_url(pn.book_vs, page, publisher_a.pk, child.pk))
    assert response.status_code == 200
    contexts = {key: ctx for key, ctx in records if key in ("create", "create_alias")}
    assert set(contexts) == {"create", "create_alias"}
    for ctx in contexts.values():
        assert ctx["cv_access"] is create_grant
        assert ctx["cv_action_enabled"] is True
        assert ctx["cv_url"] == create_url  # bound to the URL parent
    # original label context: the alias keeps its own label, the view key keeps the target default
    assert contexts["create_alias"]["cv_action_label"] == "Another book"
    assert contexts["create"]["cv_action_label"] != "Another book"
    assert (f'href="{create_url}"' in response.content.decode()) is create_grant
    _assert_hook_saw_only_parent(pn, publisher_a)

    permission, button = _render_filter_and_button(response)
    assert permission == str(create_grant)
    assert (create_url in button) is create_grant


@pytest.mark.django_db
def test_child_page_disabled_state_is_distinct_from_permission_denial(pn, client, monkeypatch, publisher_a, child):
    from tests.test1.app.models import Book

    _strict_policy(pn, monkeypatch)
    records = _record_contexts(monkeypatch, pn.BookDetail)
    detail_url = _url(pn.book_vs, "detail", publisher_a.pk, child.pk)
    create_url = _url(pn.book_vs, "create", publisher_a.pk)

    # authorized but state-disabled: permission True, state False, button unavailable, direct requests 403
    pn.state["enabled"] = False
    client.force_login(_child_page_actor(pn, publisher_a, child, create_grant=True, name="granted"))
    response = client.get(detail_url)
    for key in ("create", "create_alias"):
        (ctx,) = [c for k, c in records if k == key]
        assert ctx["cv_access"] is True
        assert ctx["cv_action_enabled"] is False
    assert f'href="{create_url}"' not in response.content.decode()
    permission, button = _render_filter_and_button(response)
    assert permission == "True"  # the permission filter stays permission-only
    assert create_url not in button
    assert client.get(create_url).status_code == 403
    assert client.post(create_url, {"title": "Disabled"}).status_code == 403
    _assert_hook_saw_only_parent(pn, publisher_a)

    # denied: both fields reflect it independently; filter False, button unavailable, direct requests 403
    records.clear()
    pn.state["enabled"] = True
    client.force_login(_child_page_actor(pn, publisher_a, child, create_grant=False, name="denied"))
    response = client.get(detail_url)
    for key in ("create", "create_alias"):
        (ctx,) = [c for k, c in records if k == key]
        assert ctx["cv_access"] is False
        assert ctx["cv_action_enabled"] is True
    permission, button = _render_filter_and_button(response)
    assert permission == "False"
    assert create_url not in button
    assert client.get(create_url).status_code == 403
    assert client.post(create_url, {"title": "Denied"}).status_code == 403
    assert not Book.objects.filter(title__in=["Disabled", "Denied"]).exists()

    # allowed + enabled: control available and the direct request agrees, bound to the URL parent
    client.force_login(_child_page_actor(pn, publisher_a, child, create_grant=True, name="allowed"))
    assert f'href="{create_url}"' in client.get(detail_url).content.decode()
    assert client.get(create_url).status_code == 200
    assert client.post(create_url, {"title": "Allowed"}).status_code == 302
    assert Book.objects.get(title="Allowed").publisher_id == publisher_a.pk


@pytest.mark.django_db
def test_child_page_create_revocation_applies_next_request(pn, client, monkeypatch, publisher_a, child):
    from tests.test1.app.models import Book

    _strict_policy(pn, monkeypatch)
    user = _child_page_actor(pn, publisher_a, child, create_grant=True)
    client.force_login(user)
    detail_url = _url(pn.book_vs, "detail", publisher_a.pk, child.pk)
    create_url = _url(pn.book_vs, "create", publisher_a.pk)
    assert f'href="{create_url}"' in client.get(detail_url).content.decode()

    pn.pub_vs.remove_perm("change", user, publisher_a)
    response = client.get(detail_url)
    assert response.status_code == 200
    assert f'href="{create_url}"' not in response.content.decode()
    assert client.post(create_url, {"title": "Revoked"}).status_code == 403
    assert not Book.objects.filter(title="Revoked").exists()


@pytest.mark.parametrize("accept_global", [True, False])
@pytest.mark.django_db
def test_child_page_create_global_fallback_follows_create_view_policy(
    pn, client, monkeypatch, publisher_a, child, accept_global
):
    _strict_policy(pn, monkeypatch)
    monkeypatch.setattr(pn.BookCreate, "cv_guardian_accept_global_perms", accept_global, raising=False)
    user = _grant_global(_child_page_actor(pn, publisher_a, child, create_grant=False), "change_publisher")
    client.force_login(user)
    create_url = _url(pn.book_vs, "create", publisher_a.pk)

    response = client.get(_url(pn.book_vs, "detail", publisher_a.pk, child.pk))
    assert (f'href="{create_url}"' in response.content.decode()) is accept_global
    assert client.get(create_url).status_code == (200 if accept_global else 403)
    assert pn.BookCreate.cv_has_access(user, child) is accept_global


@pytest.mark.django_db
def test_child_page_none_policy_create_needs_no_parent_grant(pn, client, monkeypatch, publisher_a, child):
    records = _record_contexts(monkeypatch, pn.BookDetail)
    user = _user("object_only")
    user_guardian_object_perm(user, pn.book_vs, "view", child)
    client.force_login(user)
    create_url = _url(pn.book_vs, "create", publisher_a.pk)

    response = client.get(_url(pn.book_vs, "detail", publisher_a.pk, child.pk))
    assert response.status_code == 200
    for key in ("create", "create_alias"):
        (ctx,) = [c for k, c in records if k == key]
        assert ctx["cv_access"] is True
        assert ctx["cv_action_enabled"] is True
    assert f'href="{create_url}"' in response.content.decode()
    _assert_hook_saw_only_parent(pn, publisher_a)


@pytest.mark.django_db
def test_child_page_inactive_actor_denied(pn, client, monkeypatch, publisher_a, child):
    backend = "django.contrib.auth.backends.AllowAllUsersModelBackend"
    _strict_policy(pn, monkeypatch)
    user = _child_page_actor(pn, publisher_a, child, create_grant=True)
    user.is_active = False
    user.save()
    with override_settings(AUTHENTICATION_BACKENDS=[backend, "guardian.backends.ObjectPermissionBackend"]):
        client.force_login(user, backend=backend)
        assert client.get(_url(pn.book_vs, "detail", publisher_a.pk, child.pk)).status_code == 403
    assert pn.BookCreate.cv_has_access(user, child) is False
    assert pn.BookCreate._cv_action_enabled_for_context(user, child) is True  # state is not permission
    assert pn.hook_calls and pn.hook_calls[-1].pk == publisher_a.pk


# ── card actions ──────────────────────────────────────────────────────────────


def _record_card_actions(monkeypatch, card_cls):
    records: list = []
    original = card_cls.cv_get_card_action_data

    def spy(self, action, obj, user):
        data = original(self, action, obj, user)
        records.append((action.key or action.child_name, obj, data))
        return data

    monkeypatch.setattr(card_cls, "cv_get_card_action_data", spy)
    return records


@pytest.mark.parametrize("create_grant", [True, False])
@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.django_db
def test_child_card_row_create_action_uses_row_parent(
    pn, client, monkeypatch, publisher_a, child, create_grant, enabled
):
    _strict_policy(pn, monkeypatch)
    pn.state["enabled"] = enabled
    records = _record_card_actions(monkeypatch, pn.BookCard)
    client.force_login(_child_page_actor(pn, publisher_a, child, create_grant=create_grant))
    create_url = _url(pn.book_vs, "create", publisher_a.pk)

    response = client.get(_url(pn.book_vs, "card", publisher_a.pk))
    assert response.status_code == 200
    (row,) = [data for key, obj, data in records if key == "create"]
    assert row["cv_access"] is create_grant
    assert row["cv_action_enabled"] is enabled
    assert row["cv_url"] == create_url
    assert row["cv_label"] == "Sibling book"
    (detail,) = [data for key, obj, data in records if key == "detail"]
    assert detail["cv_access"] is True  # the other card action keeps its own row-object semantics
    assert ("Sibling book" in response.content.decode()) is (create_grant and enabled)
    _assert_hook_saw_only_parent(pn, publisher_a)


@pytest.mark.django_db
def test_parent_card_child_create_action_uses_row(pn, client, monkeypatch, publisher_a, publisher_b):
    """Preservation: the child-name branch already passes the row, which is the parent."""
    from tests.test1.app.models import Publisher

    _strict_policy(pn, monkeypatch)
    records = _record_card_actions(monkeypatch, pn.PublisherCard)
    user = _user("pub_card")
    for publisher in (publisher_a, publisher_b):
        user_guardian_object_perm(user, pn.pub_vs, "view", publisher)
    user_guardian_object_perm(user, pn.pub_vs, "change", publisher_a)
    client.force_login(user)

    response = client.get(reverse(pn.pub_vs.get_router_name("card")))
    assert response.status_code == 200
    access = {obj.pk: data["cv_access"] for key, obj, data in records}
    assert access == {publisher_a.pk: True, publisher_b.pk: False}
    assert _url(pn.book_vs, "create", publisher_a.pk) in response.content.decode()
    assert _url(pn.book_vs, "create", publisher_b.pk) not in response.content.decode()
    assert all(type(obj) is Publisher for obj in pn.hook_calls)


# ── controls: the default adapter leaves other action objects unchanged ───────


def _spy_state(monkeypatch, cls):
    calls: list = []

    @classmethod
    def spy(klass, user, obj=None):
        calls.append(obj)
        return True

    monkeypatch.setattr(cls, "cv_action_enabled", spy)
    return calls


@pytest.mark.django_db
def test_core_detail_page_state_hook_receives_page_object(client_user_author_view, monkeypatch, author_douglas_adams):
    from tests.test1.app.models import Author
    from tests.test1.app.views import AuthorUpdateView

    calls = _spy_state(monkeypatch, AuthorUpdateView)
    assert client_user_author_view.get(f"/author/{author_douglas_adams.pk}/detail/").status_code == 200
    assert calls and all(type(obj) is Author and obj.pk == author_douglas_adams.pk for obj in calls)


@pytest.mark.django_db
def test_guardian_top_level_page_and_card_state_hooks_receive_row(
    client_guardian, user_guardian, cv_guardian_author, monkeypatch, author_douglas_adams
):
    from tests.test1.app.models import Author
    from tests.test1.app.views import GuardianAuthorUpdateView

    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    calls = _spy_state(monkeypatch, GuardianAuthorUpdateView)
    assert client_guardian.get(f"/guardian_author/{author_douglas_adams.pk}/detail/").status_code == 200
    assert client_guardian.get("/guardian_author/card/").status_code == 200
    assert calls and all(type(obj) is Author and obj.pk == author_douglas_adams.pk for obj in calls)
