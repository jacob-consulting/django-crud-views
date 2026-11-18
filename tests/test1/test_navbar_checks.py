"""Navbar E280 declaration, E281 attachment, E282 target, E283 duplicate, E284 template checks."""

import importlib
import sys
import types
from contextlib import contextmanager

import pytest
from django.core.checks import run_checks
from django.test import override_settings
from django.urls import URLResolver, clear_url_caches, get_resolver
from django.urls.resolvers import RoutePattern

from crud_views import checks as system_checks
from crud_views.lib.navbar import CrudViewNavBarMixin, NavBar, NavItem
from crud_views.lib.views import DetailView, ListView
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Publisher
from tests.test1.test_navbar import navbar_routes, owner_routes, section_routes

NAV_IDS = {f"viewset.E{code}" for code in range(280, 285)}
pytestmark = pytest.mark.django_db


def navbar_messages(messages):
    return [m for m in messages if m.id in NAV_IDS]


def direct_checks(cls):
    return [m for check in cls.checks() for m in check.messages()]


def test_unknown_owner_has_named_startup_error(django_assert_num_queries):
    with navbar_routes(owner_routes) as ns:
        ns.view.cv_navbar = NavBar(viewset="missing_owner", items=[NavItem(key="detail")])
        with django_assert_num_queries(0):
            errors = navbar_messages(system_checks.check_viewsets())
        assert errors, "a completed startup check must reject an unknown navbar owner"
        assert any("NavbarDetail" in m.msg and "missing_owner" in m.msg and "bar" in m.msg for m in errors)


@pytest.mark.parametrize(
    "case",
    [
        "unknown_child",
        "nondirect_child",
        "owner_key",
        "child_key",
        "explicit_list",
        "owner_no_object_target",
        "child_object_target",
        "owner_duplicate",
        "child_duplicate",
        "post_only",
        "get_excluded",
        "get_noncallable",
        "owner_list",
        "owner_card",
        "owner_create",
        "owner_custom",
        "unrelated",
        "malformed",
        "empty_item",
        "empty_owner",
        "empty_child",
        "empty_key",
        "missing_template",
    ],
)
def test_invalid_configurations(case, django_assert_num_queries, monkeypatch):
    from crud_views.lib.views import ActionView, CreateView
    from crud_views.lib.views.card import CardListView

    def build(sfx):
        ns, routed = section_routes(sfx, card_only=case == "explicit_list")
        if case in {"owner_list", "owner_card", "owner_create", "owner_custom"}:
            base = {
                "owner_list": ListView,
                "owner_card": CardListView,
                "owner_create": CreateView,
                "owner_custom": ListView,
            }[case]
            ns.attachment = type(
                "InvalidAttachment",
                (CrudViewNavBarMixin, base),
                {
                    "cv_viewset": ns.owner,
                    "cv_navbar": ns.bar,
                    "cv_key": "invalid_attachment",
                    "cv_path": "invalid-attachment",
                },
            )
        elif case == "unrelated":
            other = ViewSet(model=Publisher, name=f"unrelated{sfx}")
            ns.attachment = type(
                "InvalidAttachment", (CrudViewNavBarMixin, DetailView), {"cv_viewset": other, "cv_navbar": ns.bar}
            )
            routed.append(other)
        else:
            ns.attachment = ns.views[(ns.owner.name, "detail")]
        if case == "post_only":
            type("OnlyPost", (ActionView,), {"cv_viewset": ns.owner, "cv_key": "post", "cv_path": "post"})
            ns.bar.items = [NavItem(key="post")]
        if case == "owner_no_object_target":
            type("OwnerList", (ListView,), {"cv_viewset": ns.owner})
            ns.bar.items = [NavItem(key="list")]
        return ns, routed

    with navbar_routes(build) as ns:
        bar = ns.bar
        replacements = {
            "unknown_child": [NavItem(child="missing_child")],
            "nondirect_child": [NavItem(child=ns.grand.name)],
            "owner_key": [NavItem(key="missing_key")],
            "child_key": [NavItem(child=ns.child.name, key="missing_key")],
            "explicit_list": [NavItem(child=ns.child.name, key="list")],
            "child_object_target": [NavItem(child=ns.child.name, key="detail")],
            "owner_duplicate": [NavItem(key="detail"), NavItem(key="detail")],
            "child_duplicate": [NavItem(child=ns.child.name, key="list"), NavItem(child=ns.child.name, key="create")],
            "empty_item": [NavItem()],
            "empty_child": [NavItem(child="")],
            "empty_key": [NavItem(child=ns.child.name, key="")],
        }
        if case in replacements:
            bar.items = replacements[case]
        if case == "empty_owner":
            bar.viewset = ""
        if case == "missing_template":
            bar.template = "navbar/does-not-exist.html"
        if case == "malformed":
            ns.attachment.cv_navbar = {"viewset": "bad"}
        if case == "get_excluded":
            ns.attachment.http_method_names = ["post"]
        if case == "get_noncallable":
            ns.attachment.get = None
        # Checks must never evaluate access/state; neither are registry validation.
        for cls in ns.views.values():
            monkeypatch.setattr(cls, "cv_has_access", classmethod(lambda *args: pytest.fail("startup access hook")))
            monkeypatch.setattr(
                cls, "_cv_action_enabled_for_rendering", classmethod(lambda *args: pytest.fail("startup state hook"))
            )
        with django_assert_num_queries(0):
            messages = navbar_messages(system_checks.check_viewsets())
        named = [m for m in messages if ns.attachment.__name__ in m.msg]
        assert named, case
        assert all("navbar" in m.msg.lower() and (bar.viewset in m.msg or case == "malformed") for m in named)
        if case in replacements or case in {"get_excluded", "get_noncallable", "post_only", "owner_no_object_target"}:
            assert any("item" in m.msg and "key=" in m.msg for m in named)
        else:
            assert any("bar" in m.msg for m in named)


@pytest.mark.parametrize("option", ["valid", "none", "empty_items", "custom_template", "forgotten"])
def test_valid_checks_and_super_retention(option, django_assert_num_queries):
    with navbar_routes(section_routes) as ns:
        view = ns.views[(ns.owner.name, "detail")]
        if option == "none":
            view.cv_navbar = None
        elif option == "empty_items":
            ns.bar.items = []
        elif option == "custom_template":
            ns.bar.template = "navbar/base.html"
        elif option == "forgotten":
            view = type(
                "ForgottenMixin",
                (DetailView,),
                {"cv_viewset": ns.owner, "cv_key": "forgotten", "cv_path": "forgotten", "cv_navbar": "invalid"},
            )
        view.cv_modal_size = "invalid"  # existing super check must still run
        with django_assert_num_queries(0):
            messages = system_checks.check_viewsets()
        assert not navbar_messages(messages)
        assert any("cv_modal_size" in m.msg for m in messages)


@contextmanager
def cold_urlconf(tmp_path, monkeypatch, *, fail=False):
    """A real Python import registers views after the initial ViewSet snapshot would have been taken."""
    with navbar_routes(owner_routes) as ns:
        name = f"cold_navbar_{ns.owner.name}"
        control_name = name + "_control"
        control = types.ModuleType(control_name)
        control.owner = ns.owner
        control.attempts = 0
        control.fail = fail
        source = f"""from {control_name} import owner
import {control_name} as control
from crud_views.lib.navbar import CrudViewNavBarMixin, NavBar, NavItem
from crud_views.lib.views import DetailView
from crud_views.lib.viewset import ViewSet
control.attempts += 1
if control.fail:
    raise RuntimeError("URLconf in progress")
class LateOne(CrudViewNavBarMixin, DetailView):
    cv_viewset = owner
    cv_key = "late_one"
    cv_path = "late-one"
    cv_navbar = NavBar(viewset=owner.name, items=[NavItem(key="missing_one")])
class LateTwo(CrudViewNavBarMixin, DetailView):
    cv_viewset = owner
    cv_key = "late_two"
    cv_path = "late-two"
    cv_navbar = NavBar(viewset=owner.name, items=[NavItem(key="missing_two")])
new_owner = ViewSet(model=owner.model, name=owner.name + "new")
class LateNew(CrudViewNavBarMixin, DetailView):
    cv_viewset = new_owner
    cv_navbar = NavBar(viewset=new_owner.name, items=[NavItem(key="missing_new")])
urlpatterns = owner.urlpatterns + new_owner.urlpatterns
"""
        (tmp_path / f"{name}.py").write_text(source)
        sys.modules[control_name] = control
        monkeypatch.syspath_prepend(str(tmp_path))
        importlib.invalidate_caches()
        try:
            with override_settings(ROOT_URLCONF=name):
                clear_url_caches()
                yield ns, control
        finally:
            sys.modules.pop(name, None)
            sys.modules.pop(control_name, None)
            clear_url_caches()


@pytest.mark.parametrize("pipeline", ["direct", "django"])
def test_cold_first_completed_pass_includes_all_late_views(tmp_path, monkeypatch, pipeline, django_assert_num_queries):
    with cold_urlconf(tmp_path, monkeypatch) as (ns, control):
        assert "url_patterns" not in get_resolver().__dict__
        with django_assert_num_queries(0):
            messages = system_checks.check_viewsets() if pipeline == "direct" else run_checks(tags=[system_checks.TAG])
        errors = navbar_messages(messages)
        for cls, key in [("LateOne", "missing_one"), ("LateTwo", "missing_two"), ("LateNew", "missing_new")]:
            assert any(cls in m.msg and key in m.msg for m in errors)
        assert control.attempts == 1


def test_failed_preflight_never_retries_during_iteration(tmp_path, monkeypatch, django_assert_num_queries):
    with cold_urlconf(tmp_path, monkeypatch, fail=True) as (ns, control):
        ns.view.cv_navbar = NavBar(viewset="forward_owner", items=[NavItem(), NavItem(child="forward_child")])
        with django_assert_num_queries(0):
            messages = navbar_messages(system_checks.check_viewsets())
        assert control.attempts == 1
        assert any("item" in m.msg for m in messages)
        assert not any("unknown" in m.msg.lower() for m in messages)
        assert "url_patterns" not in get_resolver().__dict__
        control.fail = False
        messages = navbar_messages(system_checks.check_viewsets())
        assert control.attempts == 2
        assert any("forward_owner" in m.msg and "unknown" in m.msg.lower() for m in messages)
        for name in ("LateOne", "LateTwo", "LateNew"):
            assert any(name in m.msg for m in messages)


def test_probe_does_not_load_included_urlconf_and_accepts_cached_empty(monkeypatch):
    included = URLResolver(RoutePattern("included/"), "not_importable_navbar_urls")
    root = URLResolver(RoutePattern(""), [])
    root.__dict__["url_patterns"] = [included]
    monkeypatch.setattr("django.urls.get_resolver", lambda: root)
    assert system_checks._url_configuration_loaded(load=False) is False
    assert "urlconf_module" not in included.__dict__
    included.__dict__["url_patterns"] = []
    assert system_checks._url_configuration_loaded(load=False) is True


def test_early_checks_defer_forward_references():
    with navbar_routes(owner_routes) as ns:
        ns.view.cv_navbar = NavBar(viewset="future_owner", items=[NavItem(child="future_child")])
        clear_url_caches()
        assert not navbar_messages(direct_checks(ns.view))
        assert "url_patterns" not in get_resolver().__dict__
        assert navbar_messages(system_checks.check_viewsets())
