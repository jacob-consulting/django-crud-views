"""Isolated navbar SQL receipts and exact whole-response/control preservation."""

import json
from contextlib import contextmanager
from copy import copy
from unittest.mock import Mock

import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.template import Context, Template
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from guardian.shortcuts import _get_ct_cached, clear_ct_cache
from lxml import html

from crud_views.lib import check as check_module
from crud_views.lib import navbar
from crud_views.lib.ancestors import _resolved_ancestor
from crud_views.lib.navbar import CrudViewNavBarMixin
from crud_views.lib.views import DetailView
from crud_views.lib.viewset import ParentViewSet, ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.lib.helper.guardian import user_guardian_object_perm
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_guardian_child_link_visibility import sql_categories
from tests.test1.test_navbar import get_owner, navbar_routes, navbar_templates, owner_routes
from tests.test1.test_navbar_permissions import TAG, grant, permission_routes
from tests.test1.test_navbar_templates import COMPONENTS, IDENTITY, ITEMS, SPLIT


@contextmanager
def cache_conditions(viewsets, actor, *, vocabulary, actor_cache):
    """Restore pre-existing ViewSet/check vocabulary even when an assertion fails."""
    permissions = [(vs, vs._default_permissions) for vs in viewsets]
    vocabulary_before = dict(check_module._VOCAB_CACHE)
    try:
        for name in ("_perm_cache", "_user_perm_cache", "_group_perm_cache"):
            # request.user can be SimpleLazyObject: delattr forwards to the actor,
            # whereas mutating the proxy's __dict__ leaves its real caches warm.
            if hasattr(actor, name):
                delattr(actor, name)
        # These class-level admissions create fresh Guardian checkers; no persistent
        # rendering-view checker is involved. Warm actor means Django model perms only.
        if actor_cache == "warm":
            actor.get_all_permissions()
        check_module._VOCAB_CACHE.clear()
        ContentType.objects.clear_cache()
        clear_ct_cache()
        for vs in viewsets:
            vs._default_permissions = None
        if vocabulary == "warm":
            check_module._registry_vocabulary()
            for vs in viewsets:
                for permission in vs.permissions.values():
                    if permission:
                        app_label, codename = permission.split(".")
                        _get_ct_cached(app_label, codename)
                ContentType.objects.get_for_model(vs.model)
        yield
    finally:
        for vs, value in permissions:
            vs._default_permissions = value
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocabulary_before)
        ContentType.objects.clear_cache()
        clear_ct_cache()


def cost_routes(sfx, composition):
    ns, routed = permission_routes(sfx, composition=composition)
    ns.host.cv_extends_template = "navbar/without.html"
    ns.grand = ViewSet(
        model=BookNote, name=f"costnote{sfx}", parent=ParentViewSet(name=ns.child.name, attribute="book")
    )
    ns.deep = type(
        "Deep",
        (CrudViewNavBarMixin, DetailView),
        {
            "cv_viewset": ns.grand,
            "cv_navbar": ns.bar,
            "cv_extends_template": "navbar/without.html",
            "cv_context_actions": [],
        },
    )
    return ns, [*routed, ns.grand]


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["plain", "guardian", "mixed"])
@pytest.mark.parametrize("page", ["owner", "deep"])
@pytest.mark.parametrize("placement", ["tag", "split", "repeated", "components", "mixed-repeated"])
@pytest.mark.parametrize("vocabulary", ["cold", "warm"])
@pytest.mark.parametrize("actor_cache", ["cold", "warm"])
def test_navbar_isolated_costs(
    composition, page, placement, vocabulary, actor_cache, django_user_model, monkeypatch, record_property
):
    with navbar_routes(lambda sfx: cost_routes(sfx, composition)) as ns:
        owner = Publisher.objects.create(pk=101, name="Owner")
        book = Book.objects.create(pk=202, title="Child", publisher=owner)
        note = BookNote.objects.create(pk=303, note="Deep", book=book)
        actor = django_user_model.objects.create_user(username="cost")
        grant(ns, actor, owner)
        if isinstance(ns.child, GuardianViewSet):
            user_guardian_object_perm(actor, ns.child, "view", book)
        client = Client()
        client.force_login(actor)
        url = (
            reverse(ns.owner.get_router_name("host"), kwargs={"pk": owner.pk})
            if page == "owner"
            else reverse(
                ns.grand.get_router_name("detail"),
                kwargs={ns.child.parent.get_pk_name(): owner.pk, ns.grand.parent.get_pk_name(): book.pk, "pk": note.pk},
            )
        )
        build = Mock(wraps=navbar._build)
        monkeypatch.setattr(navbar, "_build", build)
        response = client.get(url)
        assert response.status_code == 200
        build.assert_not_called()
        view = response.context["view"]
        resolved_owner = view.object if page == "owner" else _resolved_ancestor(view, ns.owner.name)
        current_actor = view.request.user
        spies = []
        for target, hook in [
            (ns.detail, "cv_has_access"),
            (ns.target, "_cv_child_link_has_access"),
            (ns.detail, "_cv_action_enabled_for_rendering"),
            (ns.target, "_cv_action_enabled_for_rendering"),
        ]:
            spy = Mock(wraps=getattr(target, hook))
            monkeypatch.setattr(target, hook, spy)
            spies.append(spy)
        with cache_conditions(
            [ns.owner, ns.child, ns.grand], current_actor, vocabulary=vocabulary, actor_cache=actor_cache
        ):
            with CaptureQueriesContext(connection) as capture:
                data = view.get_context_data(object=view.object)
                context = Context(data)
                source = {"split": SPLIT, "components": COMPONENTS, "mixed-repeated": ITEMS + IDENTITY}.get(placement, TAG)
                rendered = Template(source).render(context)
                if placement in {"repeated", "mixed-repeated"}:
                    Template(TAG + SPLIT + COMPONENTS).render(copy(context))
                    Template(ITEMS + IDENTITY + TAG).render(Context(view.get_context_data(object=view.object)))
            assert rendered
            build.assert_called_once_with(view)
            for index, spy in enumerate(spies):
                spy.assert_called_once_with(current_actor, resolved_owner, *([view] if index >= 2 else []))
                assert spy.call_args.args[1] is resolved_owner
            categories = sql_categories(capture.captured_queries)
            assert categories.get("parent_rows", 0) == categories.get("child_or_relation_rows", 0) == 0
            assert not any('from "app_booknote"' in q["sql"].lower() for q in capture.captured_queries)
            assert set(categories) <= {"permissions", "content_type"}
            expected = (0 if composition == "plain" else 4) + (4 if vocabulary == "cold" else 0)
            expected += 2 if actor_cache == "cold" and composition != "guardian" else 0
            assert len(capture) == expected
            record_property(
                "measurement",
                json.dumps(
                    {
                        "composition": composition,
                        "page": page,
                        "placement": placement,
                        "vocabulary": vocabulary,
                        "actor_cache": actor_cache,
                        "queries": len(capture),
                        "categories": categories,
                        "builds": build.call_count,
                        "hooks": [spy.call_count for spy in spies],
                    },
                    sort_keys=True,
                ),
            )


@pytest.mark.django_db
@pytest.mark.parametrize("options", [{"participating": False}, {"configured": False}, {"items": False}])
def test_nonparticipant_complete_response_bytes_and_queries(options, monkeypatch):
    monkeypatch.setattr("django.middleware.csrf._get_new_csrf_string", lambda: "a" * 32)
    owner = Publisher.objects.create(name="Unchanged owner")
    with navbar_routes(lambda sfx: owner_routes(sfx, **options)) as ns:
        build = Mock(wraps=navbar._build)
        monkeypatch.setattr(navbar, "_build", build)
        forbidden = Mock(side_effect=AssertionError("nonparticipant admission"))
        monkeypatch.setattr(ns.view, "cv_has_access", forbidden)
        monkeypatch.setattr(ns.view, "_cv_action_enabled_for_rendering", forbidden)
        results = []
        for base in ("navbar/without.html", "navbar/base.html"):
            ns.view.cv_extends_template = base
            ContentType.objects.clear_cache()
            clear_ct_cache()
            with CaptureQueriesContext(connection) as capture:
                response = get_owner(ns, owner)
            assert response.status_code == 200
            results.append((response.content, [q["sql"] for q in capture.captured_queries]))
        assert results[0] == results[1]
        assert build.call_count == (1 if options.get("items") is False else 0)
        forbidden.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["omitted", "modal"])
def test_unconsumed_or_modal_has_zero_incremental_cost(mode, monkeypatch):
    owner = Publisher.objects.create(name="Unconsumed")
    with navbar_routes(owner_routes) as ns:
        forbidden = Mock(side_effect=AssertionError("unexpected navbar work"))
        monkeypatch.setattr(navbar, "_build", forbidden)
        monkeypatch.setattr(ns.view, "cv_has_access", forbidden)
        monkeypatch.setattr(ns.view, "_cv_action_enabled_for_rendering", forbidden)
        ns.view.cv_extends_template = "navbar/without.html"
        ns.view.cv_modal = mode == "modal"
        with navbar_templates({"crud_views/modal/content.html": SPLIT}):
            response = Client().get(
                reverse(ns.owner.get_router_name("detail"), kwargs={"pk": owner.pk}),
                HTTP_X_CV_MODAL="true" if mode == "modal" else "false",
            )
        assert response.status_code == 200
        view = response.context["view"]
        with CaptureQueriesContext(connection) as capture:
            data = view.get_context_data(object=view.object)
            if mode == "modal":
                assert Template(TAG + SPLIT).render(Context(data)) == "<main>Page content</main>"
        assert len(capture) == 0
        forbidden.assert_not_called()


@pytest.mark.django_db
def test_context_buttons_preserve_original_html_and_order(django_user_model, monkeypatch):
    from crud_views.lib.view import ChildContextButton

    monkeypatch.setattr("django.middleware.csrf._get_new_csrf_string", lambda: "a" * 32)
    with navbar_routes(permission_routes) as ns:
        owner = Publisher.objects.create(name="Coexist")
        actor = django_user_model.objects.create_user(username="coexist")
        grant(ns, actor, owner)
        ns.host.cv_context_buttons = [ChildContextButton(key="children", child_name=ns.child.name, label_mode="label")]
        ns.host.cv_context_actions = ["children", "detail"]
        client = Client()
        client.force_login(actor)
        url = reverse(ns.owner.get_router_name("host"), kwargs={"pk": owner.pk})
        controls = []
        for base in ("navbar/without.html", "navbar/base.html"):
            ns.host.cv_extends_template = base
            response = client.get(url)
            assert response.status_code == 200
            tree = html.fromstring(response.content)
            header = tree.xpath('//div[@class="card-header"]')[0]
            # Keep original response bytes: parsing below checks behavior/order only.
            controls.append(
                response.content.split(b'<div class="card-header">', 1)[1].split(b'<div class="card-body">', 1)[0]
            )
            assert [a.get("cv-key") for a in header.xpath(".//a[@cv-key]")] == ["list", "detail"]
            assert len(tree.xpath('//div[contains(@class,"cv-navbar ")]/nav')) == (base == "navbar/base.html")
        assert controls[0] == controls[1]
