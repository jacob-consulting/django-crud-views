"""Request-level cancel navigation, following the links actually rendered to users."""

import re
from html import unescape
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import pytest
from django.core import signing
from django_filters import FilterSet

from crud_views.lib.session import SessionData
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views.lib.views.mixins import ListViewTableFilterMixin
from tests.test1.app.models import Author


def checked_action_url(value, view, *, keep_origin=False):
    """Validate actual navigation transport before normalizing only its reserved fields."""
    from django.urls import Resolver404, resolve

    from crud_views.lib.view.cancel import clean_navigation_query, effective_cancel_keys, navigation_params

    value = unescape(value)
    parts = urlsplit(value)
    if parts.scheme or parts.netloc or not parts.path.startswith("/"):
        return value
    names = navigation_params()
    query = parse_qs(parts.query, keep_blank_values=True)
    try:
        match = resolve(parts.path)
    except Resolver404:
        return value
    target = getattr(match.func, "view_class", None)
    if target is None or not hasattr(target, "cv_cancel_keys") or target.cv_viewset is not view.cv_viewset:
        return value
    expected_origin = view.cv_get_link_origin_key(target)
    if not expected_origin or expected_origin not in effective_cancel_keys(target):
        assert names[1] not in query
        return value
    assert names[1] in query, f"missing captured origin on {value}"
    assert query[names[0]] == [expected_origin]
    assert len(query[names[1]]) == 1
    payload = signing.Signer(salt="crud_views.cancel.v1").unsign_object(query[names[1]][0])
    assert payload == {
        "v": 1,
        "origin": expected_origin,
        "query": clean_navigation_query(view.request.GET).urlencode(),
        "viewset": [view.cv_viewset.app or "", view.cv_viewset.name],
        "parents": {key: str(view.kwargs[key]) for key in view.cv_viewset.get_parent_url_args()},
    }
    for name in names[1:] if keep_origin else names:
        query.pop(name, None)
    return urlunsplit(parts._replace(query=urlencode(query, doseq=True)))


def checked_action_markup(response):
    from html import escape

    view = response.context["view"]
    return re.sub(
        r'href="([^"]+)"',
        lambda match: 'href="' + escape(checked_action_url(match[1], view), quote=True) + '"',
        response.content.decode(),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("source", "target"),
    [("list", "update"), ("list", "create"), ("list", "delete"), ("detail", "update"), ("detail", "delete")],
)
def test_default_five_routes(client_user_author_origin, cv_author, author_douglas_adams, source, target):
    from django.urls import reverse

    before = list(Author.objects.values())
    kwargs = {"pk": author_douglas_adams.pk}
    origin = reverse(cv_author.get_router_name(source), kwargs=kwargs if source == "detail" else {})
    destination = reverse(cv_author.get_router_name(target), kwargs={} if target == "create" else kwargs)
    page = client_user_author_origin.get(origin + "?sort=last_name&x=&x=two")
    link = emitted_link(page, destination)
    assert parse_qs(urlsplit(link).query)["cv_from"] == [source]
    form = client_user_author_origin.get(link)
    assert form.context["view"].cv_cancel_keys == "auto"
    cancel = rendered_cancel(form)
    assert urlsplit(cancel).path == origin
    query = parse_qs(urlsplit(cancel).query, keep_blank_values=True)
    assert query["x"] == ["", "two"]
    assert query.get("cv_from_restore") == (["1"] if source == "list" else None)
    assert client_user_author_origin.get(cancel).status_code == 200
    assert list(Author.objects.values()) == before


def emitted_link(response, path):
    links = [unescape(link) for link in re.findall(r'href="([^"]+)"', response.content.decode())]
    return next(link for link in links if urlsplit(link).path == path)


def rendered_cancel(response):
    node = re.search(r'data-cv-cancel-url="([^"]+)"', response.content.decode())
    assert node is not None, "resolved Cancel must be rendered"
    return unescape(node.group(1))


@pytest.mark.django_db
@pytest.mark.parametrize("keys", [None, [], ["detail", "detail"]])
def test_explicit_keys_are_fresh_and_repeatable(
    client_user_author_origin, cv_author, author_douglas_adams, keys, monkeypatch
):
    from crud_views.lib.view.cancel import effective_cancel_keys

    cls = cv_author.get_view_class("update")
    monkeypatch.setattr(cls, "cv_cancel_keys", keys)
    page = client_user_author_origin.get(f"/author/{author_douglas_adams.pk}/detail/?x=1")
    link = emitted_link(page, f"/author/{author_douglas_adams.pk}/update/")
    query = parse_qs(urlsplit(link).query)
    assert ("cv_from_cancel" in query) is bool(keys)
    form = client_user_author_origin.get(link)
    view = form.context["view"]
    expected = f"/author/{author_douglas_adams.pk}/detail/?x=1" if keys else "/author/"
    assert view.cv_get_cancel_url() == view.cv_get_cancel_url() == expected
    assert effective_cancel_keys(view) == (("detail",) if keys else ())
    assert cls.cv_cancel_keys == keys
    view.cv_cancel_keys = None
    assert effective_cancel_keys(view) == ()
    assert cls.cv_cancel_keys == keys


def test_auto_defaults_follow_registration_and_mro(cv_author, monkeypatch):
    from crud_views.lib import viewset as viewset_module
    from crud_views.lib.view.cancel import effective_cancel_keys
    from crud_views.lib.views import ListView, UpdateView
    from crud_views.lib.viewset import ViewSet
    from tests.test1.test_cancel_origin import check_ids

    # Late registration belongs to this test, not the process-wide form inventory.
    monkeypatch.setattr(viewset_module, "_REGISTRY", dict(viewset_module._REGISTRY))
    viewset = ViewSet(model=Author, name="cancel_late_registry")

    class LateForm(UpdateView):
        cv_viewset = viewset
        fields = ["first_name"]

    assert effective_cancel_keys(LateForm) == ()

    class LateList(ListView):
        cv_viewset = viewset

    assert effective_cancel_keys(LateForm) == ("list",)
    assert "viewset.E252" not in check_ids(LateForm)
    assert LateList.cv_cancel_keys is None
    assert LateForm.cv_cancel_keys == "auto"
    instance = LateForm()
    instance.cv_cancel_keys = None
    assert effective_cancel_keys(instance) == ()
    for invalid in ("detail", [1], {"list": True}):
        monkeypatch.setattr(LateForm, "cv_cancel_keys", invalid)
        assert "viewset.E252" in check_ids(LateForm)


@pytest.mark.django_db
def test_emitted_list_update_round_trip(
    client_user_author_origin, cv_author_origin, author_douglas_adams, author_terry_pratchett, monkeypatch
):
    from django.test import override_settings
    from django.urls import path

    original = cv_author_origin.get_view_class("list")

    class AuthorFilter(FilterSet):
        class Meta:
            model = Author
            fields = ["last_name"]

    class FilteredAuthors(ListViewTableFilterMixin, original):
        cv_viewset = None
        filterset_class = AuthorFilter
        formhelper_class = ListViewFilterFormHelper

    monkeypatch.setattr(FilteredAuthors, "cv_viewset", cv_author_origin)
    monkeypatch.setattr(cv_author_origin.get_view_class("update"), "cv_cancel_keys", "auto")
    from django.urls import reverse

    from tests.test1.app.urls import urlpatterns

    before = list(Author.objects.order_by("pk").values())
    list_url = reverse(cv_author_origin.get_router_name("list"))
    with override_settings(
        ROOT_URLCONF=type(
            "URLs", (), {"urlpatterns": [path(list_url.lstrip("/"), FilteredAuthors.as_view()), *urlpatterns]}
        )
    ):
        response = client_user_author_origin.get(list_url + "?last_name=Adams")
        assert response.status_code == 200
        view = response.context["view"]
        update = emitted_link(response, view.cv_get_url("update", author_douglas_adams))
        query = parse_qs(urlsplit(update).query)
        assert "cv_from_cancel" in query, "rendered Update link must own its captured query"
        payload = signing.Signer(salt="crud_views.cancel.v1").unsign_object(query["cv_from_cancel"][0])
        assert payload["query"] == "last_name=Adams", "decoded capture"
        form = client_user_author_origin.get(update)
        cancel = rendered_cancel(form)
        assert parse_qs(urlsplit(cancel).query) == {"last_name": ["Adams"], "cv_from_restore": ["1"]}
        client_user_author_origin.get(list_url + "?last_name=Pratchett")
        returned = client_user_author_origin.get(cancel)
        assert list(returned.context["object_list"]) == [author_douglas_adams], "returned records"
        assert SessionData.from_view(returned.context["view"]).get("filter_query_string") == "last_name=Adams"
    assert list(Author.objects.order_by("pk").values()) == before, "Cancel performs no model writes"
