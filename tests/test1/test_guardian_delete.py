import pytest

from tests.lib.helper.guardian import user_guardian_object_perm


@pytest.mark.django_db
def test_guardian_per_object_filtering(client_guardian, user_guardian, cv_guardian_publisher, publisher_a):
    """Guardian delete view filters related objects by per-object view permission."""
    from tests.test1.app.models import Book
    from tests.test1.app.views import cv_guardian_book, cv_guardian_publisher_cascade

    book_visible = Book.objects.create(title="Visible Book", publisher=publisher_a)
    Book.objects.create(title="Hidden Book", publisher=publisher_a)

    # Grant per-object delete on publisher (needed to access the delete page)
    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    # Grant per-object view on only one book
    user_guardian_object_perm(user_guardian, cv_guardian_book, "view", book_visible)

    pk = publisher_a.pk
    response = client_guardian.get(f"/guardian_publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Visible Book" in content
    assert "Hidden Book" not in content


@pytest.mark.django_db
def test_guardian_delete_still_works(client_guardian, user_guardian, cv_guardian_publisher, publisher_a):
    """Guardian delete with cv_show_related_objects=True still deletes successfully."""
    from tests.test1.app.models import Publisher
    from tests.test1.app.views import cv_guardian_publisher_cascade

    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    pk = publisher_a.pk
    response = client_guardian.post(f"/guardian_publisher_cascade/{pk}/delete/", {"confirm": True})
    assert response.status_code == 302
    assert not Publisher.objects.filter(pk=pk).exists()


# ── cv_filter_related_objects, called directly ────────────────────────────────


def _contract(publisher, title):
    from tests.test1.app.models import Contract

    return Contract.objects.create(title=title, publisher=publisher)


def _grant_contract(user, contract):
    from tests.test1.app.views import cv_contract

    user_guardian_object_perm(user, cv_contract, "view", contract)


@pytest.mark.django_db
def test_filter_related_objects_empty_tree_still_filters_protected(user_guardian, publisher_a):
    """No empty-tree shortcut: a protected-only projection is filtered by object permission, in order,
    without mutating the source collection."""
    from crud_views.lib.views.delete import RelatedObjects
    from crud_views_guardian.lib.views import GuardianDeleteRelatedObjectsMixin

    first, hidden, last = _contract(publisher_a, "C"), _contract(publisher_a, "A"), _contract(publisher_a, "B")
    _grant_contract(user_guardian, first)
    _grant_contract(user_guardian, last)
    source = [first, hidden, last]
    related = RelatedObjects(tree=[], summary={}, protected=source)

    mixin = GuardianDeleteRelatedObjectsMixin()
    result = mixin.cv_filter_related_objects(user_guardian, related)

    assert result.tree == []
    assert result.summary == {}
    assert result.protected == [first, last]
    assert related.protected is source
    assert source == [first, hidden, last]
    # idempotent: a second projection yields the same permitted subsequence
    assert mixin.cv_filter_related_objects(user_guardian, related).protected == [first, last]

    empty = RelatedObjects(tree=[], summary={}, protected=[])
    assert mixin.cv_filter_related_objects(user_guardian, empty) == RelatedObjects(tree=[], summary={}, protected=[])


@pytest.mark.django_db
def test_filter_related_objects_hides_unpermitted_and_keeps_structure(
    user_guardian, cv_guardian_publisher, publisher_a, publisher_b
):
    """Permitted objects stay, unpermitted ones become None, non-model entries
    (e.g. the string labels Django's collector emits) and nesting are preserved;
    protected objects are projected by their own object permission."""
    from crud_views.lib.views.delete import RelatedObjects
    from crud_views_guardian.lib.views import GuardianDeleteRelatedObjectsMixin

    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "view", publisher_a)
    visible, hidden = _contract(publisher_a, "Visible Contract"), _contract(publisher_b, "Hidden Contract")
    _grant_contract(user_guardian, visible)
    related = RelatedObjects(
        tree=[publisher_a, ["label", publisher_b, [publisher_a]], None],
        summary={"x": 1},
        protected=[hidden, visible],
    )

    result = GuardianDeleteRelatedObjectsMixin().cv_filter_related_objects(user_guardian, related)

    assert result.tree == [publisher_a, ["label", None, [publisher_a]], None]
    assert result.summary == {"x": 1}
    assert result.protected == [visible]
    assert related.protected == [hidden, visible]


@pytest.mark.django_db
def test_filter_related_objects_identical_labels_keep_object_identity(user_guardian, publisher_a):
    """Two protected objects with the same label: only the granted one (by pk) survives."""
    from crud_views.lib.views.delete import RelatedObjects
    from crud_views_guardian.lib.views import GuardianDeleteRelatedObjectsMixin

    granted, ungranted = _contract(publisher_a, "Same Title"), _contract(publisher_a, "Same Title")
    _grant_contract(user_guardian, granted)
    related = RelatedObjects(tree=[], summary={}, protected=[ungranted, granted])
    result = GuardianDeleteRelatedObjectsMixin().cv_filter_related_objects(user_guardian, related)
    assert [obj.pk for obj in result.protected] == [granted.pk]


# ── protected previews through real Guardian requests (D-07/D-08) ─────────────

DANGER_ALERT = 'class="alert alert-danger" role="alert"'
BLOCKED_HEADING = "Deletion is blocked by protected relationships:"


def _norm(html: str) -> str:
    import re

    return re.sub(r"\s+", " ", html)


def _response_instances(response, model) -> list:
    def walk(value, depth=0):
        if depth > 8:
            return []
        if isinstance(value, model):
            return [value]
        if isinstance(value, dict):
            return [hit for v in value.values() for hit in walk(v, depth + 1)]
        if isinstance(value, (list, tuple, set)):
            return [hit for v in value for hit in walk(v, depth + 1)]
        return []

    return [hit for layer in response.context for hit in walk(layer.flatten())]


def _context_contracts(response) -> list:
    from tests.test1.app.models import Contract

    return _response_instances(response, Contract)


def _delete_page(client, publisher, **kwargs):
    return client.get(f"/guardian_publisher_cascade/{publisher.pk}/delete/", **kwargs)


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["get", "modal", "post"])
@pytest.mark.parametrize("superuser", [False, True], ids=["object-granted", "superuser"])
def test_guardian_m2m_delete_preview_and_post(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a, monkeypatch, superuser, operation
):
    """M2M through rows cannot crash previews or POST; only active superusers see their labels."""
    from django.contrib.auth.models import User

    from tests.test1.app.models import Genre, Publisher
    from tests.test1.app.views import GuardianPublisherCascadeDeleteView, cv_guardian_publisher_cascade

    if superuser:
        actor = User.objects.create_superuser(username="m2m_superuser", email="", password="password")
        client_guardian.force_login(actor)
    else:
        user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    genre = Genre.objects.create(name="Surviving Genre")
    genre.publishers.add(publisher_a)
    through = Genre.publishers.through
    through_row = through.objects.get(publisher=publisher_a)
    publisher_pk, through_pk = publisher_a.pk, through_row.pk

    if operation == "post":
        response = client_guardian.post(f"/guardian_publisher_cascade/{publisher_pk}/delete/", {"confirm": True})
        assert response.status_code == 302
        assert not Publisher.objects.filter(pk=publisher_pk).exists()
        assert not through.objects.filter(pk=through_pk).exists()
        assert Genre.objects.filter(pk=genre.pk).exists()
    else:
        headers = {}
        if operation == "modal":
            monkeypatch.setattr(GuardianPublisherCascadeDeleteView, "cv_modal", True)
            headers["X-CV-Modal"] = "true"
        response = _delete_page(client_guardian, publisher_a, headers=headers)
        assert response.status_code == 200
        assert response.context["has_protected_objects"] is False
        content = _norm(response.content.decode())
        if superuser:
            assert through_row in _response_instances(response, through)
            assert str(through_row) in content
        else:
            assert _response_instances(response, through) == []
            assert str(through_row) not in content


@pytest.mark.django_db
@pytest.mark.parametrize("superuser", [False, True], ids=["object-granted", "superuser"])
def test_guardian_protected_model_without_view_permission(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a, superuser
):
    """A no-view model stays blocked, with labels hidden for ordinary users and visible to superusers."""
    from django.contrib.auth.models import Permission, User

    from tests.test1.app.models import Royalty
    from tests.test1.app.views import cv_guardian_publisher_cascade

    royalty = Royalty.objects.create(publisher=publisher_a, title="Secret Royalty")
    assert not Permission.objects.filter(
        content_type__app_label=Royalty._meta.app_label,
        content_type__model=Royalty._meta.model_name,
        codename="view_royalty",
    ).exists()
    if superuser:
        actor = User.objects.create_superuser(username="royalty_superuser", email="", password="password")
        client_guardian.force_login(actor)
    else:
        user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    response = _delete_page(client_guardian, publisher_a)
    assert response.status_code == 200
    assert response.context["has_protected_objects"] is True
    content = _norm(response.content.decode())
    if superuser:
        assert response.context["protected_objects"] == [royalty]
        assert royalty in _response_instances(response, Royalty)
        assert royalty.title in content
    else:
        assert response.context["protected_objects"] == []
        assert _response_instances(response, Royalty) == []
        assert royalty.title not in content
    assert content.count(DANGER_ALERT) == 1


@pytest.mark.django_db
def test_guardian_protected_only_hidden_keeps_single_notice(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a
):
    from tests.test1.app.views import cv_guardian_publisher_cascade

    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    _contract(publisher_a, "Secret Contract")
    response = _delete_page(client_guardian, publisher_a)
    assert response.status_code == 200
    assert response.context["related_summary"] == {}
    assert response.context["protected_objects"] == []
    assert response.context["has_protected_objects"] is True
    assert _context_contracts(response) == []
    content = _norm(response.content.decode())
    assert content.count(DANGER_ALERT) == 1
    assert BLOCKED_HEADING in content
    assert "Secret Contract" not in content


@pytest.mark.django_db
def test_guardian_protected_only_hidden_modal(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a, monkeypatch
):
    from tests.test1.app.views import GuardianPublisherCascadeDeleteView, cv_guardian_publisher_cascade

    monkeypatch.setattr(GuardianPublisherCascadeDeleteView, "cv_modal", True)
    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    _contract(publisher_a, "Secret Contract")
    response = _delete_page(client_guardian, publisher_a, headers={"X-CV-Modal": "true"})
    assert response.status_code == 200
    assert response.context["has_protected_objects"] is True
    assert _context_contracts(response) == []
    content = _norm(response.content.decode())
    assert content.count(DANGER_ALERT) == 1
    assert "Secret Contract" not in content


@pytest.mark.django_db
def test_guardian_protected_partial_grant_keeps_order_and_aggregates(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a
):
    from tests.test1.app.models import Book
    from tests.test1.app.views import cv_guardian_publisher_cascade

    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    Book.objects.create(title="Cascade Book", publisher=publisher_a)
    visible = _contract(publisher_a, "Visible Contract")
    _contract(publisher_a, "Hidden Contract")
    _grant_contract(user_guardian, visible)
    response = _delete_page(client_guardian, publisher_a)
    assert response.status_code == 200
    assert response.context["protected_objects"] == [visible]
    assert response.context["has_protected_objects"] is True
    assert response.context["related_summary"] == {"book": 1}
    content = _norm(response.content.decode())
    assert content.count(DANGER_ALERT) == 1
    assert "<li>Visible Contract</li>" in content
    assert "Hidden Contract" not in content


@pytest.mark.django_db
def test_guardian_protected_full_grant_and_group_grant(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a
):
    from django.contrib.auth.models import Group
    from guardian.shortcuts import assign_perm

    from tests.test1.app.views import cv_contract, cv_guardian_publisher_cascade

    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    by_user, by_group = _contract(publisher_a, "User Contract"), _contract(publisher_a, "Group Contract")
    _grant_contract(user_guardian, by_user)
    group = Group.objects.create(name="contract_viewers")
    user_guardian.groups.add(group)
    assign_perm(cv_contract.permissions["view"], group, by_group)
    response = _delete_page(client_guardian, publisher_a)
    assert sorted(response.context["protected_objects"], key=lambda c: c.pk) == [by_user, by_group]
    content = _norm(response.content.decode())
    assert content.count(DANGER_ALERT) == 1
    assert "User Contract" in content
    assert "Group Contract" in content


@pytest.mark.django_db
def test_guardian_protected_object_grant_needs_no_global_permission(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a
):
    """An object grant keeps its label even without the model-level view permission (no core re-filter)."""
    from tests.test1.app.views import cv_guardian_publisher_cascade

    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    contract = _contract(publisher_a, "Object Granted Contract")
    _grant_contract(user_guardian, contract)
    assert not user_guardian.has_perm("app.view_contract")
    response = _delete_page(client_guardian, publisher_a)
    assert response.context["protected_objects"] == [contract]


@pytest.mark.django_db
def test_guardian_protected_global_permission_follows_view_fallback(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a, monkeypatch
):
    """A global view_contract only reveals labels when the delete view accepts global permissions."""
    from django.contrib.auth.models import Permission

    from tests.test1.app.views import GuardianPublisherCascadeDeleteView, cv_guardian_publisher_cascade

    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    contract = _contract(publisher_a, "Globally Visible Contract")
    user_guardian.user_permissions.add(Permission.objects.get(codename="view_contract"))

    strict = _delete_page(client_guardian, publisher_a)
    assert strict.context["protected_objects"] == []
    assert strict.context["has_protected_objects"] is True
    assert "Globally Visible Contract" not in strict.content.decode()

    monkeypatch.setattr(GuardianPublisherCascadeDeleteView, "cv_guardian_accept_global_perms", True)
    fallback = _delete_page(client_guardian, publisher_a)
    assert fallback.context["protected_objects"] == [contract]
    assert "Globally Visible Contract" in fallback.content.decode()


@pytest.mark.django_db
def test_guardian_protected_label_escaped(client_guardian, user_guardian, cv_guardian_publisher, publisher_a):
    from tests.test1.app.views import cv_guardian_publisher_cascade

    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    contract = _contract(publisher_a, "<script>alert('Ünïcødé')</script>")
    _grant_contract(user_guardian, contract)
    content = _delete_page(client_guardian, publisher_a).content.decode()
    assert "<script>alert(" not in content
    assert "&lt;script&gt;alert(&#x27;Ünïcødé&#x27;)&lt;/script&gt;" in content


@pytest.mark.django_db
def test_guardian_protected_revocation_applies_next_request(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a
):
    from guardian.shortcuts import remove_perm

    from tests.test1.app.views import cv_contract, cv_guardian_publisher_cascade

    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    contract = _contract(publisher_a, "Revocable Contract")
    _grant_contract(user_guardian, contract)
    assert "Revocable Contract" in _delete_page(client_guardian, publisher_a).content.decode()

    remove_perm(cv_contract.permissions["view"], user_guardian, contract)
    response = _delete_page(client_guardian, publisher_a)
    assert response.context["protected_objects"] == []
    assert response.context["has_protected_objects"] is True
    content = _norm(response.content.decode())
    assert "Revocable Contract" not in content
    assert content.count(DANGER_ALERT) == 1


@pytest.mark.django_db
def test_guardian_database_protect_post_raises_and_keeps_storage(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a
):
    """Hidden protection never turns into permission to delete: confirmed POST still raises ProtectedError."""
    from django.db.models import ProtectedError

    from tests.test1.app.models import Contract, Publisher
    from tests.test1.app.views import cv_guardian_publisher_cascade

    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    contract = _contract(publisher_a, "Secret Contract")
    with pytest.raises(ProtectedError):
        client_guardian.post(f"/guardian_publisher_cascade/{publisher_a.pk}/delete/", {"confirm": True})
    assert Publisher.objects.filter(pk=publisher_a.pk).exists()
    assert Contract.objects.filter(pk=contract.pk).exists()


# ── AUTH-01: HTTP DELETE is rejected before object lookup (D-01/D-02) ─────────


def _allow(response) -> set[str]:
    return {m.strip() for m in response.headers.get("Allow", "").split(",") if m.strip()}


def _spy_get_object(monkeypatch, view_class) -> list:
    calls = []
    original = view_class.get_object

    def spy(self, *args, **kwargs):
        calls.append(self.request.method)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(view_class, "get_object", spy)
    return calls


@pytest.mark.django_db
def test_guardian_http_delete_rejected_with_grant(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a, monkeypatch
):
    from tests.test1.app.models import Publisher
    from tests.test1.app.views import GuardianPublisherCascadeDeleteView, cv_guardian_publisher_cascade

    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    lookups = _spy_get_object(monkeypatch, GuardianPublisherCascadeDeleteView)
    response = client_guardian.delete(f"/guardian_publisher_cascade/{publisher_a.pk}/delete/")
    assert response.status_code == 405
    assert "DELETE" not in _allow(response)
    assert {"GET", "POST", "OPTIONS"} <= _allow(response)
    assert lookups == []
    assert Publisher.objects.filter(pk=publisher_a.pk).exists()


@pytest.mark.django_db
def test_guardian_http_delete_rejected_without_grant_or_target(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a, monkeypatch
):
    """Active top-level Guardian actors reach 405 before object lookup, regardless of grant or target existence."""
    from tests.test1.app.models import Publisher
    from tests.test1.app.views import GuardianPublisherCascadeDeleteView

    lookups = _spy_get_object(monkeypatch, GuardianPublisherCascadeDeleteView)
    assert client_guardian.delete(f"/guardian_publisher_cascade/{publisher_a.pk}/delete/").status_code == 405
    assert client_guardian.delete("/guardian_publisher_cascade/999999/delete/").status_code == 405
    assert lookups == []
    assert Publisher.objects.filter(pk=publisher_a.pk).exists()


@pytest.mark.django_db
def test_guardian_http_delete_anonymous_keeps_login_redirect(client, cv_guardian_publisher, publisher_a):
    from tests.test1.app.models import Publisher

    response = client.delete(f"/guardian_publisher_cascade/{publisher_a.pk}/delete/")
    assert response.status_code == 302
    assert "login" in response.headers["Location"]
    assert Publisher.objects.filter(pk=publisher_a.pk).exists()


@pytest.mark.django_db
def test_guardian_options_and_restored_method_omit_delete(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a, monkeypatch
):
    from django.views.generic import View

    from tests.test1.app.models import Publisher
    from tests.test1.app.views import GuardianPublisherCascadeDeleteView, cv_guardian_publisher_cascade

    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    url = f"/guardian_publisher_cascade/{publisher_a.pk}/delete/"
    default_options = client_guardian.options(url)
    assert default_options.status_code == 200
    assert "DELETE" not in _allow(default_options)

    monkeypatch.setattr(GuardianPublisherCascadeDeleteView, "http_method_names", list(View.http_method_names))
    lookups = _spy_get_object(monkeypatch, GuardianPublisherCascadeDeleteView)
    response = client_guardian.delete(url)
    assert response.status_code == 405
    assert "DELETE" not in _allow(response)
    options = client_guardian.options(url)
    assert "DELETE" not in _allow(options)
    assert _allow(options) == _allow(response) == _allow(default_options)
    assert lookups == []
    assert Publisher.objects.filter(pk=publisher_a.pk).exists()


@pytest.mark.django_db
def test_registered_guardian_class_restoring_delete_stays_guarded(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a, monkeypatch
):
    """A18/A22: the registered Guardian delete class, patched to list "delete" again, inherits the guard."""
    from django.views import generic
    from django.views.generic import View
    from django.views.generic.edit import DeletionMixin

    from crud_views.lib.view import CrudView
    from crud_views.lib.views.delete import _DeleteMethodGuardMixin
    from tests.test1.app.models import Publisher
    from tests.test1.app.views import GuardianPublisherCascadeDeleteView, cv_guardian_publisher_cascade

    mro = GuardianPublisherCascadeDeleteView.__mro__
    assert mro.index(CrudView) < mro.index(_DeleteMethodGuardMixin) < mro.index(generic.DeleteView)
    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    original = GuardianPublisherCascadeDeleteView.http_method_names
    url = f"/guardian_publisher_cascade/{publisher_a.pk}/delete/"
    with monkeypatch.context() as patch:
        patch.setattr(GuardianPublisherCascadeDeleteView, "http_method_names", [*View.http_method_names])
        entered = []
        raw_delete = DeletionMixin.delete
        patch.setattr(
            DeletionMixin,
            "delete",
            lambda self, request, *a, **kw: entered.append(1) or raw_delete(self, request, *a, **kw),
        )
        lookups = _spy_get_object(patch, GuardianPublisherCascadeDeleteView)
        for _ in range(2):
            response = client_guardian.delete(url)
            assert response.status_code == 405
            assert "DELETE" not in _allow(response)
        assert "DELETE" not in _allow(client_guardian.options(url))
        assert entered == []
        assert lookups == []
    assert GuardianPublisherCascadeDeleteView.http_method_names is original
    assert "delete" not in GuardianPublisherCascadeDeleteView.http_method_names
    assert Publisher.objects.filter(pk=publisher_a.pk).exists()
