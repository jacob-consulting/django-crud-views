"""Real-request navbar contract; registrations and templates are local to each test."""

import importlib.util
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.conf import settings
from django.template import Context, Template
from django.test import Client, override_settings
from django.urls import reverse
from django.utils.functional import SimpleLazyObject
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy
from lxml import html

from crud_views.lib.viewset import _REGISTRY, ViewSet
from tests.test1.app.models import Publisher
from tests.test1.test_ancestor_authorization import isolated_routes


@contextmanager
def navbar_templates(extra=None):
    base = Path("tests/test1/app/templates/app/crud_views.html").read_text()
    templates = {
        "navbar/base.html": base.replace('    <div class="card">', '{% cv_navbar %}    <div class="card">', 1),
        "navbar/without.html": base,
    }
    templates.update(extra or {})
    config = deepcopy(settings.TEMPLATES)
    config[0]["APP_DIRS"] = False
    config[0]["OPTIONS"]["loaders"] = [
        ("django.template.loaders.locmem.Loader", templates),
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    with override_settings(TEMPLATES=config):
        yield


@contextmanager
def navbar_routes(build):
    # isolated_routes preimports project URLs and restores registry/vocabulary/URL/CT caches.
    permissions = [(vs, vs._default_permissions) for vs in _REGISTRY.values()]
    try:
        with navbar_templates(), isolated_routes(build) as ns:
            yield ns
    finally:
        for vs, value in permissions:
            vs._default_permissions = value


def owner_routes(sfx, *, label=None, template_code=None, configured=True, participating=True, items=True):
    from crud_views.lib.navbar import CrudViewNavBarMixin, NavBar, NavItem
    from crud_views.lib.views import DetailView

    # The declaration intentionally precedes its owner's registration.
    bar = NavBar(viewset=f"navbar{sfx}", items=[NavItem(key="detail", label=label)] if items else [])
    owner = ViewSet(model=Publisher, name=bar.viewset)
    bases = (CrudViewNavBarMixin, DetailView) if participating else (DetailView,)
    attrs = {
        "cv_viewset": owner,
        "cv_navbar": bar if configured else None,
        "cv_extends_template": "navbar/base.html",
        "cv_context_actions": [],
        "cv_header_template": None,
        "cv_header_template_code": "Unchanged page header",
    }
    if template_code is not None:
        attrs.update(cv_action_short_label_template=None, cv_action_short_label_template_code=template_code)
    view = type("NavbarDetail", bases, attrs)
    return SimpleNamespace(owner=owner, view=view, bar=bar), [owner]


def get_owner(ns, obj):
    return Client().get(reverse(ns.owner.get_router_name("detail"), kwargs={ns.owner.pk_name: obj.pk}))


@pytest.mark.django_db
def test_real_owner_navbar():
    assert importlib.util.find_spec("crud_views.lib.navbar") is not None, "public navbar declaration module is missing"
    obj = Publisher.objects.create(name="Owner identity")
    with navbar_routes(lambda sfx: owner_routes(sfx, template_code="Details")) as ns:
        before = ns.bar.model_dump()
        response = get_owner(ns, obj)
        assert response.status_code == 200
        soup = html.fromstring(response.content)
        nav = soup.xpath('//nav[contains(@class,"cv-navbar")]')[0]
        assert nav is not None
        assert nav.xpath('.//*[@class="cv-navbar-identity"]')[0].text_content().strip() == obj.name
        link = nav.xpath(".//a")[0]
        assert link.text_content().strip() == "Details"
        assert link.get("href") == reverse(ns.owner.get_router_name("detail"), kwargs={"pk": obj.pk})
        assert link.get("aria-current") == "true"
        assert soup.xpath("//*[@data-test-page-title]")[0].text_content().strip() == "Unchanged page header"
        assert isinstance(response.context["cv_navbar"], SimpleLazyObject)
        assert ns.bar.model_dump() == before


@pytest.mark.django_db
@pytest.mark.parametrize("options", [{"configured": False}, {"participating": False}, {"items": False}])
def test_absent_navbar_preserves_page(options, monkeypatch):
    monkeypatch.setattr("django.middleware.csrf._get_new_csrf_string", lambda: "a" * 32)
    obj = Publisher.objects.create(name="Owner")
    with navbar_routes(lambda sfx: owner_routes(sfx, **options)) as ns:
        present = get_owner(ns, obj).content
        ns.view.cv_extends_template = "navbar/without.html"
        absent = get_owner(ns, obj).content
        assert present == absent


@pytest.mark.parametrize("value", [None, False, {}, []])
def test_tag_empty_output(value):
    assert Template("{% load crud_views %}{% cv_navbar %}").render(Context({"cv_navbar": value})) == ""


@pytest.mark.django_db
@pytest.mark.parametrize(
    "text", ["A & B's", "literal &amp; &#39;", mark_safe("<b>unsafe & text</b>"), gettext_lazy("Lazy & text")]
)
@pytest.mark.parametrize("default", [False, True])
def test_plain_owner_and_item_text(text, default, monkeypatch):
    obj = Publisher.objects.create(name="Owner")
    monkeypatch.setattr(Publisher, "__str__", lambda self: str(text))
    options = {"template_code": "{{ object }}"} if default else {"label": text}
    with navbar_routes(lambda sfx: owner_routes(sfx, **options)) as ns:
        response = get_owner(ns, obj)
        nav = html.fromstring(response.content).xpath('//nav[contains(@class,"cv-navbar")]')[0]
        assert nav.xpath('.//*[@class="cv-navbar-identity"]')[0].text_content().strip() == str(text)
        # A rendered safe input is decoded once by the default-label normalization contract.
        expected = str(text)
        assert nav.xpath(".//a")[0].text_content().strip() == expected
        assert not nav.xpath(".//b | .//script")
        assert "&amp;" in html.tostring(nav).decode()


@pytest.mark.django_db
def test_default_label_literal_entities():
    obj = Publisher.objects.create(name="Owner")
    with navbar_routes(lambda sfx: owner_routes(sfx, template_code="Details &amp; owner&#39;s")) as ns:
        nav = html.fromstring(get_owner(ns, obj).content).xpath('//nav[contains(@class,"cv-navbar")]')[0]
        assert nav.xpath(".//a")[0].text_content().strip() == "Details & owner's"
        assert "&amp;" in html.tostring(nav).decode()


def test_declarations_reject_non_string_references():
    from pydantic import ValidationError

    from crud_views.lib.navbar import NavBar, NavItem

    for value in [object(), lambda: "owner", 17]:
        with pytest.raises(ValidationError):
            NavBar(viewset=value, items=[])
        with pytest.raises(ValidationError):
            NavItem(child=value)


def section_routes(sfx, *, child_key=None, card_only=False, nested=False, intermediate=True):
    from crud_views.lib.ancestor_policy import AncestorPolicy
    from crud_views.lib.navbar import CrudViewNavBarMixin, NavBar, NavItem
    from crud_views.lib.views import CreateView, DetailView, ListView, UpdateView
    from crud_views.lib.views.card import CardListView
    from crud_views.lib.viewset import ParentViewSet
    from tests.test1.app.models import Book, BookNote

    bar = NavBar(
        viewset=f"owner{sfx}",
        items=[
            NavItem(key="detail"),
            NavItem(key="update", label="Edit"),
            NavItem(key="notes", label="Notes"),
            NavItem(child=f"orders{sfx}", key=child_key),
        ],
    )
    tenant = (
        ViewSet(model=Publisher, name=f"tenant{sfx}", ancestor_policy=AncestorPolicy(provider="none"))
        if nested
        else None
    )
    owner = ViewSet(
        model=Book if nested else Publisher,
        name=bar.viewset,
        pk_name="owner_pk",
        parent=ParentViewSet(name=tenant.name, attribute="publisher", pk_name="tenant_pk") if tenant else None,
        ancestor_policy=AncestorPolicy(provider="none"),
    )
    child = ViewSet(
        model=BookNote if nested else Book,
        name=f"orders{sfx}",
        verbose_name_plural="Orders",
        parent=ParentViewSet(name=owner.name, attribute="book" if nested else "publisher", pk_name="customer_pk"),
        ancestor_policy=AncestorPolicy(provider="none"),
    )
    grand = (
        None
        if nested
        else ViewSet(
            model=BookNote,
            name=f"items{sfx}",
            parent=ParentViewSet(name=child.name, attribute="book", pk_name="order_pk"),
            ancestor_policy=AncestorPolicy(provider="none"),
        )
    )
    views = {}
    labels = []

    def add(vs, key, base, *, mixin=True):
        attrs = {
            "cv_viewset": vs,
            "cv_key": key,
            "cv_path": key,
            "cv_navbar": bar,
            "cv_extends_template": "navbar/base.html",
            "cv_context_actions": [],
            "cv_list_actions": [],
            "pk_url_kwarg": vs.pk_name,
            "fields": ["name" if vs.model is Publisher else "title" if vs.model is Book else "note"],
        }
        if vs is owner and key == "detail":

            def short_label(cls, context):
                labels.append(context)
                return cls.render_snippet(cls.cv_viewset.get_meta(context), None, "{{ object }} details")

            attrs["cv_get_action_short_label"] = classmethod(short_label)
        cls = type(f"Navbar{vs.name}{key}", (CrudViewNavBarMixin, base) if mixin else (base,), attrs)
        views[(vs.name, key)] = cls
        return cls

    for key, base in [("detail", DetailView), ("update", UpdateView), ("notes", DetailView), ("other", DetailView)]:
        add(owner, key, base)
    for key, base in [
        ("card" if card_only else "list", CardListView if card_only else ListView),
        ("detail", DetailView),
        ("create", CreateView),
        ("update", UpdateView),
        ("custom", ListView),
    ]:
        add(child, key, base, mixin=intermediate)
    if grand:
        add(grand, "update", UpdateView)
    routed = [vs for vs in (tenant, owner, child, grand) if vs is not None]
    return SimpleNamespace(
        owner=owner, child=child, grand=grand, tenant=tenant, bar=bar, views=views, labels=labels
    ), routed


def section_objects(ns):
    from tests.test1.app.models import Book, BookNote

    publisher = Publisher.objects.create(pk=101, name="Tenant" if ns.tenant else "Customer")
    book = Book.objects.create(pk=202, title="Customer" if ns.tenant else "Order", publisher=publisher)
    note = BookNote.objects.create(pk=303, note="Order" if ns.tenant else "Item", book=book)
    return (book, note, None) if ns.tenant else (publisher, book, note)


def section_url(ns, vs, key, owner, child, grand):
    kwargs = {"tenant_pk": owner.publisher_id} if ns.tenant else {}
    if vs is not ns.owner:
        kwargs["customer_pk"] = owner.pk
    if vs is ns.grand:
        kwargs["order_pk"] = child.pk
    if vs.get_view_class(key).cv_object:
        kwargs[vs.pk_name] = (owner if vs is ns.owner else child if vs is ns.child else grand).pk
    return reverse(vs.get_router_name(key), kwargs=kwargs)


@pytest.mark.django_db
@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize(
    "page",
    [
        "owner.detail",
        "owner.update",
        "owner.notes",
        "owner.other",
        "child.list",
        "child.detail",
        "child.create",
        "child.update",
        "child.custom",
        "grand.update",
    ],
)
def test_same_owner_and_destinations_across_sections(nested, page):
    if nested and page == "grand.update":
        # The four-level case is covered separately with a temporary leaf model.
        page = "child.update"
    with navbar_routes(lambda sfx: section_routes(sfx, nested=nested)) as ns:
        owner, child, grand = section_objects(ns)
        which, key = page.split(".")
        vs = getattr(ns, which)
        response = Client(raise_request_exception=False).get(section_url(ns, vs, key, owner, child, grand))
        assert response.status_code == 200
        data = response.context["cv_navbar"]
        assert data["object"] == owner
        assert data["label"] == "Customer"
        assert [i["label"] for i in data["items"]] == ["Customer details", "Edit", "Notes", "Orders"]
        expected = [section_url(ns, ns.owner, k, owner, child, grand) for k in ("detail", "update", "notes")]
        expected.append(section_url(ns, ns.child, "list", owner, child, grand))
        assert [i["url"] for i in data["items"]] == expected
        active = [i["label"] for i in data["items"] if i["active"]]
        assert active == (
            {"detail": ["Customer details"], "update": ["Edit"], "notes": ["Notes"]}.get(key, [])
            if which == "owner"
            else ["Orders"]
        )
        assert ns.labels[-1].object is data["object"]
        assert ns.labels[-1].view is response.context["view"]


@pytest.mark.django_db
@pytest.mark.parametrize("key,card_only", [("create", False), ("custom", False), (None, True)])
def test_exact_child_destination(key, card_only):
    with navbar_routes(lambda sfx: section_routes(sfx, child_key=key, card_only=card_only)) as ns:
        owner, child, grand = section_objects(ns)
        response = Client().get(section_url(ns, ns.child, "detail", owner, child, grand))
        item = response.context["cv_navbar"]["items"][-1]
        assert item["url"] == section_url(ns, ns.child, key or "card", owner, child, grand)
        assert item["active"] is True
        assert Client().get(item["url"]).status_code == 200


@pytest.mark.django_db
def test_grandchild_does_not_require_intermediate_mixin():
    with navbar_routes(lambda sfx: section_routes(sfx, intermediate=False)) as ns:
        owner, child, grand = section_objects(ns)
        response = Client().get(section_url(ns, ns.grand, "update", owner, child, grand))
        assert response.context["cv_navbar"]["items"][-1]["active"] is True


@pytest.mark.django_db
def test_route_identity_overrides_extra_kwargs():
    with navbar_routes(lambda sfx: section_routes(sfx, nested=True)) as ns:
        owner, child, grand = section_objects(ns)
        ns.views[(ns.owner.name, "detail")].cv_get_url_extra_kwargs = classmethod(
            lambda cls: {"owner_pk": 999, "tenant_pk": 999}
        )
        ns.views[(ns.child.name, "list")].cv_get_url_extra_kwargs = classmethod(
            lambda cls: {"customer_pk": 999, "tenant_pk": 999}
        )
        response = Client().get(section_url(ns, ns.child, "detail", owner, child, grand))
        items = response.context["cv_navbar"]["items"]
        assert items[0]["url"] == section_url(ns, ns.owner, "detail", owner, child, grand)
        assert items[-1]["url"] == section_url(ns, ns.child, "list", owner, child, grand)
