"""Regression for G-06.18-2: a Guardian view whose permission key is missing from its ViewSet's permission map.

The example app's Note list raised guardian's opaque ``TypeError: 'NoneType' object is not iterable`` when the
database had not received the Note migration (no ``auth_permission`` rows, so ``viewset.permissions`` lacked
``"view"``). The Guardian request gates must now fail with a named ``ImproperlyConfigured`` and the render
helper must deny, for every actor including superusers; access is never granted through an absent vocabulary.
"""

from contextlib import contextmanager

import pytest
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ImproperlyConfigured
from django.test import Client
from guardian.ctypes import get_content_type

from crud_views.lib.viewset import _REGISTRY
from tests.lib.helper.guardian import user_guardian_object_perm
from tests.test1.app.views import (
    GuardianAuthorDetailView,
    cv_author,
    cv_guardian_author,
    cv_guardian_book,
    cv_guardian_publisher,
)


@contextmanager
def without_permission_key(viewset, key):
    """Remove one vocabulary key the way an unapplied migration does, then restore the ViewSet caches.

    Nonempty vocabularies are cached per process (``GuardianViewSet.default_permissions``), so the cache is
    primed and saved first, the ``Permission`` row is deleted (the test transaction restores it), and the cache
    is cleared so the next read rediscovers the reduced vocabulary from the database. The row backs every
    registered ViewSet on the same model, so all of their caches are saved and restored, not only ``viewset``'s.
    """
    assert key in viewset.permissions  # primes the per-process cache before it is saved
    saved = [(vs, vs._default_permissions) for vs in list(_REGISTRY.values()) if vs.model is viewset.model]
    content_type = get_content_type(viewset.model)
    deleted, _ = Permission.objects.filter(content_type=content_type, codename=f"{key}_{content_type.model}").delete()
    assert deleted
    viewset._default_permissions = None
    try:
        assert key not in viewset.permissions
        yield
    finally:
        for vs, cache in saved:
            vs._default_permissions = cache


def _actor(kind):
    if kind == "superuser":
        return User.objects.create_superuser(username="vocab_superuser", password="password")
    return User.objects.create_user(username="vocab_user", password="password")


def _client(user):
    client = Client()
    client.force_login(user)
    return client


# ── Case 1: top-level list gate ──────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["user", "superuser"])
def test_missing_key_list_raises_improperly_configured(kind):
    client = _client(_actor(kind))
    with without_permission_key(cv_guardian_author, "view"), pytest.raises(ImproperlyConfigured) as exc:
        client.get("/guardian_author/")
    message = str(exc.value)
    assert "'guardian_author'" in message
    assert "'view'" in message
    assert "'list'" in message
    assert "migrate" in message


# ── Case 2: top-level object gate ────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["user", "superuser"])
def test_missing_key_detail_raises_improperly_configured(kind, author_douglas_adams):
    client = _client(_actor(kind))
    with without_permission_key(cv_guardian_author, "view"), pytest.raises(ImproperlyConfigured) as exc:
        client.get(f"/guardian_author/{author_douglas_adams.pk}/detail/")
    message = str(exc.value)
    assert "'guardian_author'" in message
    assert "'view'" in message
    assert "'detail'" in message
    assert "migrate" in message


# ── Case 3: render helper denies without raising ─────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["user", "superuser"])
def test_missing_key_cv_has_access_denies(kind, author_douglas_adams):
    user = _actor(kind)
    with without_permission_key(cv_guardian_author, "view"):
        assert GuardianAuthorDetailView.cv_has_access(user, author_douglas_adams) is False
        assert GuardianAuthorDetailView.cv_has_access(user, None) is False


# ── Case 4: nested list (mirrors UAT test 2) ─────────────────────────────────


@pytest.mark.django_db
def test_missing_child_key_nested_list_names_child_viewset(
    client_guardian, user_guardian, publisher_a, book_under_publisher_a
):
    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "view", publisher_a)
    with without_permission_key(cv_guardian_book, "view"), pytest.raises(ImproperlyConfigured) as exc:
        client_guardian.get(f"/guardian_publisher/{publisher_a.pk}/guardian_book/")
    message = str(exc.value)
    assert "'guardian_book'" in message
    assert "'view'" in message
    assert "'list'" in message


# ── Case 5: paired controls with the vocabulary present ──────────────────────


@pytest.mark.django_db
def test_present_vocabulary_outcomes_unchanged(client_guardian, user_guardian, author_douglas_adams):
    assert client_guardian.get("/guardian_author/").status_code == 200

    other = User.objects.create_user(username="vocab_other", password="password")
    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    assert GuardianAuthorDetailView.cv_has_access(user_guardian, author_douglas_adams) is True
    assert GuardianAuthorDetailView.cv_has_access(other, author_douglas_adams) is False

    with pytest.raises(ValueError, match=r"^Invalid permission key 'typo'\. Valid keys: "):
        cv_guardian_author.get_objects_for_user(user_guardian, "typo")


@pytest.mark.django_db
def test_vocabulary_cache_restored_after_helper(client_guardian, author_douglas_adams):
    with without_permission_key(cv_guardian_author, "view"):
        pass
    assert "view" in cv_guardian_author.permissions
    response = client_guardian.get(f"/guardian_author/{author_douglas_adams.pk}/detail/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_helper_restores_sibling_viewsets_on_the_same_model():
    """The deleted row backs every ViewSet on ``Author``; a cold sibling read inside the block must not keep it."""
    saved = cv_author._default_permissions
    cv_author._default_permissions = None  # a sibling no earlier test has warmed
    try:
        with without_permission_key(cv_guardian_author, "view"):
            assert "view" not in cv_author.permissions  # caches the reduced vocabulary for the process
        assert cv_author._default_permissions is None  # back to cold; rediscovers once the row is restored
    finally:
        cv_author._default_permissions = saved
