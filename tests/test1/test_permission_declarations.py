"""#341: declared permission keys, both E269 halves, and their skips and zero-DB contract."""

from __future__ import annotations

import pytest
from django.core.checks import run_checks
from django.db import models
from django.test import override_settings
from django.test.utils import isolate_apps

import tests.test1.project.urls  # noqa: F401 - registers shared ViewSets before any registry snapshot
from crud_views.checks import check_ancestor_declarations, check_viewsets
from crud_views.lib.ancestors import _declared_permission_keys, _permission_key
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib.views import GuardianListViewPermissionRequired
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1 import test_ancestor_operations as _ops
from tests.test1.app.models import Book, BookNote, Car, Publisher, PublisherProxy, Royalty, WorkflowRequest
from tests.test1.app.views import cv_book
from tests.test1.test_resource_viewset import T5Item, check_error_ids

# Reuse the registry-restoring and database-blocking fixtures without collecting the source module's tests.
registry, sfx, no_db = _ops.registry, _ops.sfx, _ops.no_db
_view, _ours, _core, _nested = _ops._view, _ops._ours, _ops._core, _ops._nested


def _e269(*viewsets):
    return [
        message
        for message in check_ancestor_declarations()
        if message.id == "viewset.E269" and any(message.obj is viewset for viewset in viewsets)
    ]


def test_undeclared_cv_permission_is_reported_at_startup(registry, sfx, no_db):
    with isolate_apps("tests.test1.app"):

        class Approvable(models.Model):
            class Meta:
                app_label = "app"
                permissions = [("approve_approvable", "Can approve")]

        vs = ViewSet(model=Approvable, name=f"pd_approvable_{sfx}")
        _view(_core("ListViewPermissionRequired"), vs)
        _view(_core("ActionViewPermissionRequired"), vs, key="approve", cv_permission="approve")
        _view(_core("ActionViewPermissionRequired"), vs, key="run", cv_permission="run")

        assert _ours(check_ancestor_declarations(), vs) == [("viewset.E269", vs.name)]
        message = _e269(vs)[0]
        assert message.msg == "cv_permission 'run' of view 'run' is not declared on model app.Approvable"
        assert message.hint == (
            'add ("run_approvable", "...") to Approvable.Meta.permissions, '
            "or use the non-PermissionRequired view variant"
        )
        assert len([m for m in run_checks(tags=["crud_views"]) if m.id == "viewset.E269" and m.obj is vs]) == 1
        assert "viewset.E269" not in [m.id for c in vs.checks() for m in c.messages()]

        Approvable._meta.permissions.append(("run_approvable", "Can run"))
        assert _ours(check_ancestor_declarations(), vs) == []


def test_shared_registry_has_no_e269(no_db):
    assert [m for m in check_ancestor_declarations() if m.id == "viewset.E269"] == []


def test_declared_keys_map_default_actions_to_themselves(no_db):
    assert _declared_permission_keys(Publisher) == {"add", "change", "delete", "view"}
    assert _declared_permission_keys(Book) == {"add", "change", "delete", "view"}


def test_declared_keys_strip_only_the_terminal_model_suffix(no_db):
    with isolate_apps("tests.test1.app"):

        class Manuscript(models.Model):
            class Meta:
                app_label = "app"
                permissions = [
                    ("approve_manuscript", "Can approve"),
                    ("change_manuscript_status", "Can change the status"),
                ]

        assert _declared_permission_keys(Manuscript) == {
            "add",
            "change",
            "delete",
            "view",
            "approve",
            "change_manuscript_status",
        }
    assert _permission_key("view_book", "book") == "view"
    assert _permission_key("change_book_status", "book") == "change_book_status"
    assert _permission_key("approve", "book") == "approve"


def test_declared_keys_of_a_proxy_come_from_the_concrete_model(no_db):
    assert _declared_permission_keys(PublisherProxy) == _declared_permission_keys(Publisher)
    with isolate_apps("tests.test1.app"):

        class PubProxy(Publisher):
            class Meta:
                proxy = True
                app_label = "app"
                permissions = [("audit_pubproxy", "Can audit")]

        assert _declared_permission_keys(PubProxy) == {"add", "change", "delete", "view"}


def test_declared_keys_of_an_mti_child_are_its_own(no_db):
    assert Car._meta.concrete_model is Car
    assert _declared_permission_keys(Car) == {"add", "change", "delete", "view"}
    with isolate_apps("tests.test1.app"):

        class Craft(models.Model):
            class Meta:
                app_label = "app"
                permissions = [("fly_craft", "Can fly")]

        class Glider(Craft):
            class Meta:
                app_label = "app"

        assert "fly" in _declared_permission_keys(Craft)
        assert _declared_permission_keys(Glider) == {"add", "change", "delete", "view"}


def test_declared_keys_follow_trimmed_and_custom_meta(no_db):
    assert _declared_permission_keys(Royalty) == {"add", "change", "delete"}
    assert _declared_permission_keys(WorkflowRequest) == {"add", "change", "delete", "view", "process"}


@pytest.mark.django_db
def test_runtime_map_keys_equal_the_declared_keys():
    assert set(cv_book.permissions) == _declared_permission_keys(Book)
    assert cv_book.permissions["view"] == "app.view_book"


def test_trimmed_default_permissions_report_the_standard_message(registry, sfx, no_db):
    with isolate_apps("tests.test1.app"):

        class Ledger(models.Model):
            class Meta:
                app_label = "app"
                default_permissions = ("add", "change", "delete")

        vs = ViewSet(model=Ledger, name=f"pd_ledger_{sfx}")
        _view(_core("ListViewPermissionRequired"), vs)
        messages = _e269(vs)
        assert len(messages) == 1
        assert messages[0].msg == "cv_permission 'view' of view 'list' is not declared on model app.Ledger"
        assert messages[0].hint == (
            'add ("view_ledger", "...") to Ledger.Meta.permissions, or use the non-PermissionRequired view variant'
        )


def test_proxy_viewset_hint_names_the_concrete_model(registry, sfx, no_db):
    vs = ViewSet(model=PublisherProxy, name=f"pd_proxy_{sfx}")
    _view(_core("ActionViewPermissionRequired"), vs, key="audit", cv_permission="audit")
    messages = _e269(vs)
    assert len(messages) == 1
    assert messages[0].msg.endswith("is not declared on model app.Publisher")
    assert 'add ("audit_publisher", "...") to Publisher.Meta.permissions' in messages[0].hint


def test_unset_cv_permission_is_left_to_e202(registry, sfx, no_db):
    vs = ViewSet(model=Publisher, name=f"pd_none_{sfx}")
    _view(_core("ActionViewPermissionRequired"), vs, key="x", cv_permission=None)
    assert _e269(vs) == []
    assert "viewset.E202" in check_error_ids(vs)


def test_resource_viewset_is_left_to_e260(registry, sfx, no_db):
    vs = ViewSet(model=T5Item, name=f"pd_resource_{sfx}", resource_permissions=None)
    _view(_core("ListViewPermissionRequired"), vs)
    assert "viewset.E260" in check_error_ids(vs)
    assert _e269(vs) == []


@pytest.mark.django_db
def test_guardian_viewset_is_skipped_and_still_fails_at_request_time(registry, sfx):
    gvs = GuardianViewSet(model=Publisher, name=f"pd_guardian_{sfx}")
    List = type(
        "List",
        (GuardianListViewPermissionRequired,),
        {
            "cv_viewset": gvs,
            "cv_list_actions": [],
            "cv_context_actions": [],
            "cv_permission": "run",
            "__module__": __name__,
        },
    )
    assert _e269(gvs) == []
    # Pins the core assert; Guardian request gates instead raise ImproperlyConfigured in _local_permission_name.
    with pytest.raises(AssertionError, match="permission run not found"):
        _ = List().permission_required


def test_undeclared_cv_permission_is_deferred_until_the_urlconf_is_loaded(registry, sfx, no_db):
    vs = ViewSet(model=Publisher, name=f"pd_deferred_{sfx}")
    _view(_core("ActionViewPermissionRequired"), vs, key="run", cv_permission="run")
    with override_settings(ROOT_URLCONF=None):
        assert _e269(vs) == []
    messages = _e269(vs)
    assert len(messages) == 1
    assert "'run'" in messages[0].msg


def _chain(sfx, *, pub_policy=None, book_policy=None, note_policy=None):
    pub_vs = ViewSet(model=Publisher, name=f"pd_pub_{sfx}", ancestor_policy=pub_policy or AncestorPolicy())
    _view(_core("ListView"), pub_vs)
    book_vs = ViewSet(
        model=Book,
        name=f"pd_book_{sfx}",
        parent=ParentViewSet(name=pub_vs.name, attribute="publisher"),
        ancestor_policy=book_policy or AncestorPolicy(),
    )
    _view(_core("ListView"), book_vs)
    note_vs = ViewSet(
        model=BookNote,
        name=f"pd_note_{sfx}",
        parent=ParentViewSet(name=book_vs.name, attribute="book"),
        ancestor_policy=note_policy or AncestorPolicy(),
    )
    return pub_vs, book_vs, note_vs


def test_actions_pair_key_missing_on_the_ancestor_is_reported(registry, sfx, no_db):
    _, book_vs = _nested(
        sfx, policy=AncestorPolicy(actions={"approve": AncestorPermissions(nearest="approve", higher="view")})
    )
    _view(_core("ActionView"), book_vs, key="approve")
    _view(_core("ListView"), book_vs)
    assert _ours(check_ancestor_declarations(), book_vs) == [("viewset.E269", book_vs.name)]
    message = _e269(book_vs)[0]
    assert message.msg == (
        f"ancestor permission key 'approve' (actions['approve'].nearest) of ViewSet {book_vs.name!r} "
        "is not declared on model app.Publisher"
    )
    assert message.hint == (
        'declare ("approve_publisher", "...") in Publisher.Meta.permissions, '
        f"or change the pair on ViewSet {book_vs.name!r}"
    )
    assert len([m for m in run_checks(tags=["crud_views"]) if m.id == "viewset.E269" and m.obj is book_vs]) == 1


def test_explicit_pairs_resolve_nearest_and_higher_on_their_ancestors(registry, sfx, no_db):
    pub_vs, book_vs, note_vs = _chain(
        sfx,
        note_policy=AncestorPolicy(
            read=AncestorPermissions(nearest="audit", higher="view"),
            write=AncestorPermissions(nearest="change", higher="publish"),
        ),
    )
    _view(_core("ListView"), note_vs)
    _view(_core("DeleteView"), note_vs)
    assert sorted(m.msg for m in _e269(note_vs)) == [
        f"ancestor permission key 'audit' (ancestor_policy.read.nearest) of ViewSet {note_vs.name!r} "
        "is not declared on model app.Book",
        f"ancestor permission key 'publish' (ancestor_policy.write.higher) of ViewSet {note_vs.name!r} "
        "is not declared on model app.Publisher",
    ]
    assert _e269(pub_vs, book_vs) == []


def test_inherited_global_pair_names_the_setting_and_skips_the_resource_leaf(registry, sfx, no_db, monkeypatch):
    monkeypatch.setattr(
        crud_views_settings, "ancestor_read_permissions", AncestorPermissions(nearest="audit", higher="view")
    )
    _, book_vs = _nested(sfx)
    _view(_core("ListView"), book_vs)
    messages = check_ancestor_declarations()
    ours = [m for m in messages if m.id == "viewset.E269" and m.obj is book_vs]
    assert len(ours) == 1
    assert ours[0].msg == (
        "ancestor permission key 'audit' (global CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS.nearest) "
        f"of ViewSet {book_vs.name!r} is not declared on model app.Publisher"
    )
    assert [m for m in messages if m.id == "viewset.E269" and m.obj.name == "publisherfile"] == []
    assert [m for m in messages if m.id == "viewset.E269" and m.obj.name == "book"]


def test_default_pairs_are_silent_and_nearest_only_ignores_higher(registry, sfx, no_db):
    _, book_vs = _nested(sfx)
    _view(_core("ListView"), book_vs)
    _view(_core("DeleteView"), book_vs)
    assert _e269(book_vs) == []
    assert [m for m in check_ancestor_declarations() if m.id == "viewset.E269" and m.obj.name == "book"] == []
    _, _, note_vs = _chain(
        sfx + "n",
        note_policy=AncestorPolicy(cascade=False, read=AncestorPermissions(nearest="view", higher="publish")),
    )
    _view(_core("ListView"), note_vs)
    assert _e269(note_vs) == []


def test_one_error_per_unresolved_key_and_ancestor(registry, sfx, no_db):
    _, _, note_vs = _chain(sfx)
    _view(_core("ListView"), note_vs)
    with isolate_apps("tests.test1.app"):

        class Annotation(models.Model):
            note = models.ForeignKey(BookNote, on_delete=models.CASCADE)

            class Meta:
                app_label = "app"

        leaf_vs = ViewSet(
            model=Annotation,
            name=f"pd_leaf_{sfx}",
            parent=ParentViewSet(name=note_vs.name, attribute="note"),
            ancestor_policy=AncestorPolicy(
                read=AncestorPermissions(nearest="view", higher="publish"),
                actions={"stamp": AncestorPermissions(nearest="view", higher="publish")},
            ),
        )
        _view(_core("ListView"), leaf_vs)
        _view(_core("ActionView"), leaf_vs, key="stamp")
        assert sorted(m.msg.split(" is not declared on model ")[1] for m in _e269(leaf_vs)) == [
            "app.Book",
            "app.Publisher",
        ]
        assert sorted(m.msg for m in _e269(leaf_vs)) == [
            f"ancestor permission key 'publish' (ancestor_policy.read.higher) of ViewSet {leaf_vs.name!r} "
            "is not declared on model app.Book",
            f"ancestor permission key 'publish' (ancestor_policy.read.higher) of ViewSet {leaf_vs.name!r} "
            "is not declared on model app.Publisher",
        ]


def test_guardian_checked_viewset_and_guardian_ancestors_are_skipped(registry, sfx, no_db):
    _, gbook = _nested(
        sfx + "c",
        policy=AncestorPolicy(read=AncestorPermissions(nearest="audit", higher="view")),
        viewset_cls=GuardianViewSet,
    )
    _view(_core("ListView"), gbook)
    assert _e269(gbook) == []

    gpub = GuardianViewSet(model=Publisher, name=f"pd_gpub_{sfx}")
    gpub_model = GuardianViewSet(
        model=Publisher, name=f"pd_gpubm_{sfx}", ancestor_policy=AncestorPolicy(provider="model")
    )
    core_pub = ViewSet(model=Publisher, name=f"pd_corepub_{sfx}")
    for index, parent in enumerate((gpub, gpub_model, core_pub)):
        child = ViewSet(
            model=Book,
            name=f"pd_gchild{index}_{sfx}",
            parent=ParentViewSet(name=parent.name, attribute="publisher"),
            ancestor_policy=AncestorPolicy(read=AncestorPermissions(nearest="audit", higher="view")),
        )
        _view(_core("ListView"), child)
        if parent is core_pub:
            messages = _e269(child)
            assert len(messages) == 1
            assert "'audit'" in messages[0].msg
        else:
            assert _e269(child) == []


def test_none_ancestor_is_not_checked_and_does_not_consume_nearest(registry, sfx, no_db):
    _, _, note_vs = _chain(
        sfx,
        book_policy=AncestorPolicy(provider="none"),
        note_policy=AncestorPolicy(read=AncestorPermissions(nearest="audit", higher="publish")),
    )
    _view(_core("ListView"), note_vs)
    assert [m.msg for m in _e269(note_vs)] == [
        f"ancestor permission key 'audit' (ancestor_policy.read.nearest) of ViewSet {note_vs.name!r} "
        "is not declared on model app.Publisher"
    ]
    _, _, note_ctl = _chain(
        sfx + "p", note_policy=AncestorPolicy(read=AncestorPermissions(nearest="audit", higher="publish"))
    )
    _view(_core("ListView"), note_ctl)
    assert sorted(m.msg.split(" is not declared on model ")[1] for m in _e269(note_ctl)) == [
        "app.Book",
        "app.Publisher",
    ]
    _, book_none, _ = _chain(
        sfx + "a",
        pub_policy=AncestorPolicy(provider="none"),
        book_policy=AncestorPolicy(read=AncestorPermissions(nearest="audit", higher="audit")),
    )
    assert _e269(book_none) == []


def test_unclassified_endpoint_without_entry_is_e268_only(registry, sfx, no_db):
    _, book_vs = _nested(sfx)
    _view(_core("ActionView"), book_vs, key="approve")
    assert _ours(check_ancestor_declarations(), book_vs) == [("viewset.E268", book_vs.name)]


def test_pairs_are_checked_only_through_registered_views(registry, sfx, no_db):
    with isolate_apps("tests.test1.app"):

        class Imprint(models.Model):
            class Meta:
                app_label = "app"
                default_permissions = ("add", "delete", "view")

        class Leaflet(models.Model):
            imprint = models.ForeignKey(Imprint, on_delete=models.CASCADE)

            class Meta:
                app_label = "app"

        imprint_vs = ViewSet(model=Imprint, name=f"pd_imprint_{sfx}")
        _view(_core("ListView"), imprint_vs)
        readonly = ViewSet(
            model=Leaflet,
            name=f"pd_leaflet_{sfx}",
            parent=ParentViewSet(name=imprint_vs.name, attribute="imprint"),
        )
        _view(_core("ListView"), readonly)
        assert _e269(readonly) == []
        explicit = ViewSet(
            model=Leaflet,
            name=f"pd_leaflet2_{sfx}",
            parent=ParentViewSet(name=imprint_vs.name, attribute="imprint"),
            ancestor_policy=AncestorPolicy(write=AncestorPermissions(nearest="publish", higher="view")),
        )
        _view(_core("ListView"), explicit)
        assert _e269(explicit) == []
        _view(_core("DeleteView"), explicit)
        assert [m.msg for m in _e269(explicit)] == [
            f"ancestor permission key 'publish' (ancestor_policy.write.nearest) of ViewSet {explicit.name!r} "
            "is not declared on model app.Imprint"
        ]
        assert _e269(readonly) == []


@pytest.mark.django_db
def test_checks_query_no_database(django_assert_num_queries):
    with django_assert_num_queries(0):
        ancestor_messages = check_ancestor_declarations()
        view_messages = check_viewsets()
    assert [m for m in [*ancestor_messages, *view_messages] if m.id == "viewset.E269"] == []
