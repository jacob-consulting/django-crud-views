"""Real-request navbar contract; registrations and templates are local to each test."""

import importlib.util
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
from lxml import html
from django.conf import settings
from django.template import Context, Template
from django.test import Client, override_settings
from django.urls import reverse
from django.utils.functional import SimpleLazyObject
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy

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
    attrs = dict(cv_viewset=owner, cv_navbar=bar if configured else None, cv_extends_template="navbar/base.html",
                 cv_context_actions=[], cv_header_template=None, cv_header_template_code="Unchanged page header")
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
    with navbar_routes(owner_routes) as ns:
        before = ns.bar.model_dump()
        response = get_owner(ns, obj)
        assert response.status_code == 200
        soup = html.fromstring(response.content)
        nav = soup.xpath('//nav[contains(@class,"cv-navbar")]')[0]
        assert nav is not None
        assert nav.xpath('.//*[@class="cv-navbar-identity"]')[0].text_content().strip() == obj.name
        link = nav.xpath('.//a')[0]
        assert link.text_content().strip() == "Details"
        assert link.get("href") == reverse(ns.owner.get_router_name("detail"), kwargs={"pk": obj.pk})
        assert link.get("aria-current") == "true"
        assert soup.xpath('//*[@data-test-page-title]')[0].text_content().strip() == "Unchanged page header"
        assert isinstance(response.context["cv_navbar"], SimpleLazyObject)
        assert ns.bar.model_dump() == before


@pytest.mark.django_db
@pytest.mark.parametrize("options", [{"configured": False}, {"participating": False}, {"items": False}])
def test_absent_navbar_preserves_page(options):
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
@pytest.mark.parametrize("text", ["A & B's", "literal &amp; &#39;", mark_safe('<b>unsafe & text</b>'), gettext_lazy("Lazy & text")])
@pytest.mark.parametrize("default", [False, True])
def test_plain_owner_and_item_text(text, default, monkeypatch):
    obj = Publisher.objects.create(name="Owner")
    monkeypatch.setattr(Publisher, "__str__", lambda self: text)
    options = {"template_code": "{{ object }}"} if default else {"label": text}
    with navbar_routes(lambda sfx: owner_routes(sfx, **options)) as ns:
        response = get_owner(ns, obj)
        nav = html.fromstring(response.content).xpath('//nav[contains(@class,"cv-navbar")]')[0]
        assert nav.xpath('.//*[@class="cv-navbar-identity"]')[0].text_content().strip() == str(text)
        # A rendered safe input is decoded once by the default-label normalization contract.
        expected = str(text)
        assert nav.xpath('.//a')[0].text_content().strip() == expected
        assert not nav.xpath('.//b | .//script')
        assert "&amp;" in html.tostring(nav).decode()


@pytest.mark.django_db
def test_default_label_literal_entities():
    obj = Publisher.objects.create(name="Owner")
    with navbar_routes(lambda sfx: owner_routes(sfx, template_code="Details &amp; owner&#39;s")) as ns:
        nav = html.fromstring(get_owner(ns, obj).content).xpath('//nav[contains(@class,"cv-navbar")]')[0]
        assert nav.xpath('.//a')[0].text_content().strip() == "Details & owner's"
        assert "&amp;" in html.tostring(nav).decode()


def test_declarations_reject_non_string_references():
    from pydantic import ValidationError
    from crud_views.lib.navbar import NavBar, NavItem

    for value in [object(), lambda: "owner", 17]:
        with pytest.raises(ValidationError):
            NavBar(viewset=value, items=[])
        with pytest.raises(ValidationError):
            NavItem(child=value)
