"""AC-16: bulk forms reuse ordinary origin, cancel and success navigation."""

from unittest.mock import Mock
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import pytest
from django.contrib import messages
from django.contrib.auth.models import Permission, User
from django.contrib.messages import get_messages
from django.urls import reverse

from crud_views.lib.bulk import BulkFormViewPermissionRequired
from crud_views.lib.button_classes import get_button_class
from crud_views.lib.view.cancel import navigation_params
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy
from tests.test1.app.models import Publisher
from tests.test1.app.views_bulk import BulkFilterListView, BulkFilterMarkView, BulkPublisherListView
from tests.test1.test_ancestor_authorization import _client, isolated_routes
from tests.test1.test_bulk_flow import soup
from tests.test1.test_link_consumer_costs import consumer_actor, consumer_routes, consumer_view, consumer_world

pytestmark = pytest.mark.django_db


@pytest.fixture
def return_publishers():
    return [Publisher.objects.create(name=name) for name in ("Other", *(f"Match {letter}" for letter in "ABCDEF"))]


def url(viewset, key):
    return reverse(viewset.get_router_name(key))


def source_action(client, viewset, key, *, filtered=True, action="mark"):
    query = {"sort": "-name", "page": "2"} if key == "list" else {"order": "name", "dir": "desc", "page": "2"}
    if filtered:
        query["name"] = "Match"
    source = url(viewset, key) + "?" + urlencode(query)
    response = client.get(source)
    assert response.status_code == 200
    page = soup(response)
    selected = page.cssselect("input[data-cv-bulk-item]")
    assert len(selected) == 2
    formaction = page.cssselect(f'[data-cv-bulk-action="{action}"]')[0].get("formaction")
    assert formaction
    return source, formaction, selected[0].get("value")


def assert_source_url(actual, expected):
    actual_parts, expected_parts = urlsplit(actual), urlsplit(expected)
    assert not actual_parts.scheme and not actual_parts.netloc
    assert actual_parts.path == expected_parts.path
    query = parse_qs(actual_parts.query)
    query.pop(navigation_params()[2], None)
    assert query == parse_qs(expected_parts.query)


def cancel_control(response):
    assert response.status_code == 200
    controls = soup(response).cssselect("[data-cv-cancel-url]")
    assert len(controls) == 1
    return controls[0]


def assert_warning(response, expected):
    assert response.status_code == 302
    assert [(message.level, str(message)) for message in get_messages(response.wsgi_request)] == [
        (messages.WARNING, expected)
    ]


@pytest.mark.parametrize("source_key", ["list", "card"])
def test_cancel_restores_filtered_sorted_page_two(
    client_user_bulk_filter_change, cv_bulk_filter, return_publishers, source_key
):
    client = client_user_bulk_filter_change
    source, action, selected = source_action(client, cv_bulk_filter, source_key)
    response = client.post(action, {"cv_bulk_stage": "review", "cv_bulk_ids": [selected]})
    target = cancel_control(response).get("data-cv-cancel-url")
    assert_source_url(target, source)
    returned = client.get(target)
    assert returned.status_code == 200
    assert returned.context["page_obj"].number == 2
    assert returned.context["filter"].form["name"].value() == "Match"
    assert [item.get("value") for item in soup(returned).cssselect("input[data-cv-bulk-item]")] == [
        str(return_publishers[4].pk),
        str(return_publishers[3].pk),
    ]


@pytest.mark.parametrize("source_key", ["list", "card"])
def test_empty_selection_warning_restores_filtered_sorted_page_two(
    client_user_bulk_filter_change, cv_bulk_filter, return_publishers, source_key
):
    client = client_user_bulk_filter_change
    source, action, _ = source_action(client, cv_bulk_filter, source_key)
    response = client.post(action, {"cv_bulk_stage": "review"})
    assert_warning(response, "Select at least one record.")
    assert_source_url(response["Location"], source)


@pytest.mark.parametrize("source_key", ["list", "card"])
def test_plain_get_restores_filtered_sorted_page_two_without_message(
    client_user_bulk_filter_change, cv_bulk_filter, return_publishers, source_key
):
    client = client_user_bulk_filter_change
    source, action, _ = source_action(client, cv_bulk_filter, source_key)
    response = client.get(action)
    assert response.status_code == 302
    assert_source_url(response["Location"], source)
    assert list(get_messages(response.wsgi_request)) == []


@pytest.mark.parametrize("source_key", ["list", "card"])
def test_success_with_declared_origins_returns_to_plain_source_url(
    client_user_bulk_filter_change, cv_bulk_filter, return_publishers, source_key, monkeypatch
):
    monkeypatch.setattr(BulkFilterMarkView, "cv_success_keys", ["list", "card"])
    client = client_user_bulk_filter_change
    _, action, selected = source_action(client, cv_bulk_filter, source_key)
    response = client.post(action, {"cv_bulk_stage": "execute", "cv_bulk_ids": [selected]})
    assert response.status_code == 302
    assert response["Location"] == url(cv_bulk_filter, source_key)
    assert Publisher.objects.get(pk=selected).name.endswith(" (marked)")


@pytest.mark.parametrize("source_key", ["list", "card"])
def test_success_without_declared_origins_uses_static_target(
    client_user_bulk_filter_change, cv_bulk_filter, return_publishers, source_key, monkeypatch
):
    assert BulkFormViewPermissionRequired.cv_success_keys is None
    assert BulkFilterMarkView.cv_success_keys is None
    # A different target for each origin makes accidental origin routing fail.
    target = "card" if source_key == "list" else "list"
    monkeypatch.setattr(BulkFilterMarkView, "cv_success_key", target)
    client = client_user_bulk_filter_change
    _, action, selected = source_action(client, cv_bulk_filter, source_key)
    response = client.post(action, {"cv_bulk_stage": "execute", "cv_bulk_ids": [selected]})
    assert response.status_code == 302
    assert response["Location"] == url(cv_bulk_filter, target)


@pytest.mark.parametrize("source_key", ["list", "card"])
def test_success_return_restores_persisted_filter(
    client_user_bulk_filter_change, cv_bulk_filter, return_publishers, source_key, monkeypatch
):
    monkeypatch.setattr(BulkFilterMarkView, "cv_success_keys", ["list", "card"])
    client = client_user_bulk_filter_change
    source, action, selected = source_action(client, cv_bulk_filter, source_key)
    response = client.post(action, {"cv_bulk_stage": "execute", "cv_bulk_ids": [selected]}, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain[0] == (url(cv_bulk_filter, source_key), 302)
    assert_source_url(response.redirect_chain[1][0], source)
    assert response.context["filter"].form["name"].value() == "Match"
    assert response.context["page_obj"].number == 2
    assert all(row.name.startswith("Match") for row in response.context["object_list"])
    assert return_publishers[0] not in response.context["filter"].qs


def test_success_without_filter_persistence_returns_to_first_page_default_order(
    client_user_bulk_publisher_change, cv_bulk_publisher, return_publishers, monkeypatch
):
    monkeypatch.setattr(BulkPublisherListView, "paginate_by", 2)
    client = client_user_bulk_publisher_change
    _, action, selected = source_action(client, cv_bulk_publisher, "list", filtered=False, action="archive")
    response = client.post(action, {"cv_bulk_stage": "execute", "cv_bulk_ids": [selected]}, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url(cv_bulk_publisher, "list"), 302)]
    assert response.context["page_obj"].number == 1
    assert [item.get("value") for item in soup(response).cssselect("input[data-cv-bulk-item]")] == [
        str(return_publishers[1].pk),
        str(return_publishers[2].pk),
    ]


def test_unaccepted_source_uses_cancel_fallback_without_query_state(
    client_user_bulk_filter_change, cv_bulk_filter, return_publishers, monkeypatch
):
    monkeypatch.setattr(BulkFilterMarkView, "cv_cancel_keys", ["card"])
    assert BulkFilterMarkView.cv_success_keys is None
    client = client_user_bulk_filter_change
    _, action, selected = source_action(client, cv_bulk_filter, "list")
    assert navigation_params()[0] not in parse_qs(urlsplit(action).query)
    target = url(cv_bulk_filter, BulkFilterMarkView.cv_cancel_key)
    review = client.post(action, {"cv_bulk_stage": "review", "cv_bulk_ids": [selected]})
    assert cancel_control(review).get("data-cv-cancel-url") == target
    plain_get = client.get(action)
    assert plain_get.status_code == 302
    assert plain_get["Location"] == target
    assert list(get_messages(plain_get.wsgi_request)) == []
    warning = client.post(action, {"cv_bulk_stage": "review"})
    assert_warning(warning, "Select at least one record.")
    assert warning["Location"] == target


def test_success_only_origin_does_not_capture_cancel_state(
    client_user_bulk_filter_change, cv_bulk_filter, return_publishers, monkeypatch
):
    monkeypatch.setattr(BulkFilterMarkView, "cv_cancel_keys", ["card"])
    monkeypatch.setattr(BulkFilterMarkView, "cv_cancel_key", "card")
    monkeypatch.setattr(BulkFilterMarkView, "cv_success_keys", ["list"])
    monkeypatch.setattr(BulkFilterMarkView, "cv_success_key", "card")
    client = client_user_bulk_filter_change
    _, action, selected = source_action(client, cv_bulk_filter, "list")
    origin, token, _ = navigation_params()
    query = parse_qs(urlsplit(action).query)
    assert query[origin] == ["list"]
    assert token not in query
    review = client.post(action, {"cv_bulk_stage": "review", "cv_bulk_ids": [selected]})
    assert cancel_control(review).get("data-cv-cancel-url") == url(cv_bulk_filter, "card")
    plain_get = client.get(action)
    assert plain_get.status_code == 302
    assert plain_get["Location"] == url(cv_bulk_filter, "card")
    assert list(get_messages(plain_get.wsgi_request)) == []
    warning = client.post(action, {"cv_bulk_stage": "review"})
    assert_warning(warning, "Select at least one record.")
    assert warning["Location"] == url(cv_bulk_filter, "card")
    success = client.post(action, {"cv_bulk_stage": "execute", "cv_bulk_ids": [selected]})
    assert success.status_code == 302
    assert success["Location"] == url(cv_bulk_filter, "list")


@pytest.mark.parametrize("with_origin", [True, False])
def test_back_url_falls_back_to_success_url_without_cancel_target(
    client_user_bulk_filter_change, cv_bulk_filter, return_publishers, monkeypatch, with_origin
):
    client = client_user_bulk_filter_change
    _, action, selected = source_action(client, cv_bulk_filter, "list")
    monkeypatch.setattr(BulkFilterMarkView, "cv_success_key", "card")
    monkeypatch.setattr(BulkFilterListView, "cv_has_access", classmethod(lambda cls, user, obj=None: False))
    if not with_origin:
        action = urlsplit(action).path
    target = url(cv_bulk_filter, "card")
    response = client.get(action)
    assert response.status_code == 302
    assert response["Location"] == target
    assert list(get_messages(response.wsgi_request)) == []
    empty = client.post(action, {"cv_bulk_stage": "review"})
    assert_warning(empty, "Select at least one record.")
    assert empty["Location"] == target
    # Render the redirect target to consume the warning through normal middleware.
    assert client.get(target, follow=True).status_code == 200
    monkeypatch.setattr(BulkFilterMarkView, "cv_bulk_max", 1)
    oversized = client.post(action, {"cv_bulk_stage": "review", "cv_bulk_ids": [selected, return_publishers[0].pk]})
    assert_warning(oversized, "Select at most 1 record.")
    assert oversized["Location"] == target


def test_all_blocked_cancel_button_falls_back_to_success_url_without_cancel_target(
    client_user_bulk_filter_change, cv_bulk_filter, return_publishers, monkeypatch
):
    client = client_user_bulk_filter_change
    source, action, _ = source_action(client, cv_bulk_filter, "list", filtered=False)
    missing_pk = max(row.pk for row in return_publishers) + 1
    data = {"cv_bulk_stage": "review", "cv_bulk_ids": [missing_pk]}
    review = client.post(action, data)
    assert_source_url(cancel_control(review).get("data-cv-cancel-url"), source)
    assert "This item is unavailable for this action." in soup(review).text_content()
    assert not soup(review).cssselect('button[type="submit"]')
    monkeypatch.setattr(BulkFilterMarkView, "cv_success_key", "card")
    monkeypatch.setattr(BulkFilterListView, "cv_has_access", classmethod(lambda cls, user, obj=None: False))
    fallback = client.post(action, data)
    control = cancel_control(fallback)
    assert control.tag == "button"
    assert control.text_content().strip() == "Cancel"
    assert control.get("class") == get_button_class("form", "cancel")
    assert control.get("data-cv-cancel-url") == url(cv_bulk_filter, "card")
    assert not soup(fallback).cssselect('button[type="submit"]')


@pytest.mark.parametrize("forged", ["https://attacker.example/elsewhere", "garbage"])
def test_forged_return_token_uses_local_cancel_fallback(
    client_user_bulk_filter_change, cv_bulk_filter, return_publishers, forged
):
    client = client_user_bulk_filter_change
    _, action, _ = source_action(client, cv_bulk_filter, "card")
    parts = urlsplit(action)
    query = parse_qs(parts.query)
    token_name = navigation_params()[1]
    assert token_name in query
    query[token_name] = [forged]
    action = urlunsplit(parts._replace(query=urlencode(query, doseq=True)))
    response = client.post(action, {"cv_bulk_stage": "review"})
    assert_warning(response, "Select at least one record.")
    location = urlsplit(response["Location"])
    assert not location.scheme and not location.netloc
    assert response["Location"] == url(cv_bulk_filter, BulkFilterMarkView.cv_cancel_key)


@pytest.fixture
def nested_bulk_return(monkeypatch, settings):
    """Capture a real origin before revocation; bulk uses a less strict far gate."""
    settings.CRUD_VIEWS_BUTTON_CLASSES = {"form:cancel-tag": "a"}
    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        ns.note.vs.ancestor_policy = AncestorPolicy(
            cascade=True,
            actions={
                "list": AncestorPermissions(nearest="view", higher="change"),
                "card": AncestorPermissions(nearest="view", higher="view"),
                "mark": AncestorPermissions(nearest="change", higher="view"),
            },
        )
        monkeypatch.setattr(ns.note.Bulk, "cv_cancel_keys", ["list"])
        monkeypatch.setattr(ns.note.Bulk, "cv_cancel_key", "card")
        monkeypatch.setattr(ns.note.Bulk, "cv_success_key", "source")
        page = consumer_view(ns.note, "List", actor, world)
        query = [
            ("sort", "-note"),
            ("page", "1"),
            ("tag", "first"),
            ("tag", "second"),
            *zip(navigation_params(), ("stale", "invalid", "1"), strict=True),
        ]
        response = _client(actor).get(page.cv_get_url("list") + "?" + urlencode(query))
        assert response.status_code == 200
        action = response.context_data["view"].cv_get_link_url(ns.note.Bulk, "mark")
        assert parse_qs(urlsplit(action).query)[navigation_params()[0]] == ["list"]
        assert navigation_params()[1] in parse_qs(urlsplit(action).query)
        yield ns, world, actor, page, action


@pytest.mark.parametrize("surface", ["get", "warning", "all-blocked"])
@pytest.mark.parametrize("choice", ["origin", "fallback", "success"])
def test_nested_bulk_return_uses_cancel_ancestor_eligibility(nested_bulk_return, surface, choice, monkeypatch):
    ns, world, actor, page, action = nested_bulk_return
    if choice == "success":
        ns.note.vs.ancestor_policy = ns.note.vs.ancestor_policy.model_copy(
            update={
                "actions": {
                    **ns.note.vs.ancestor_policy.actions,
                    "card": AncestorPermissions(nearest="view", higher="change"),
                }
            }
        )
    if choice != "origin":
        actor.user_permissions.remove(Permission.objects.get(codename="change_publisher"))
        actor = User.objects.get(pk=actor.pk)
    client = _client(actor)
    # The actor retains both the bulk endpoint's own grant and its distinct
    # ancestor requirements; eligibility must not bypass request authorization.
    assert actor.has_perm(ns.note.vs.permissions["change"])
    assert client.get(page.cv_get_url("list")).status_code == (200 if choice == "origin" else 403)
    assert client.get(page.cv_get_url("card")).status_code == (403 if choice == "success" else 200)
    expected = page.cv_get_url({"origin": "list", "fallback": "card", "success": "source"}[choice])
    if choice == "origin":
        expected += "?" + urlencode(
            [("sort", "-note"), ("page", "1"), ("tag", "first"), ("tag", "second"), (navigation_params()[2], "1")]
        )
    writes = Mock(side_effect=AssertionError("Return navigation executed a bulk write"))
    monkeypatch.setattr(ns.note.Bulk, "cv_form_valid", writes)
    if surface == "get":
        response = client.get(action)
        assert response.status_code == 302
        assert list(get_messages(response.wsgi_request)) == []
        actual = response["Location"]
    elif surface == "warning":
        response = client.post(action, {"cv_bulk_stage": "review"})
        assert_warning(response, "Select at least one record.")
        actual = response["Location"]
    else:
        monkeypatch.setattr(ns.note.Bulk, "cv_bulk_check", lambda self, obj: ["Locked for this action."])
        response = client.post(action, {"cv_bulk_stage": "review", "cv_bulk_ids": [world.note.pk]})
        assert response.status_code == 200
        controls = soup(response).xpath("//a[normalize-space(.)='Cancel']")
        assert len(controls) == 1
        control = controls[0]
        assert control.tag == "a"
        assert control.get("data-cv-cancel-url") is None
        assert control.text_content().strip() == "Cancel"
        assert "Locked for this action." in soup(response).text_content()
        assert not soup(response).cssselect('button[type="submit"]')
        assert list(get_messages(response.wsgi_request)) == []
        actual = control.get("href")
    assert actual == expected
    assert not urlsplit(actual).netloc
    assert navigation_params()[0] not in parse_qs(urlsplit(actual).query)
    assert navigation_params()[1] not in parse_qs(urlsplit(actual).query)
    if choice != "origin":
        assert urlsplit(actual).query == ""
    writes.assert_not_called()
    world.note.refresh_from_db()
    assert world.note.note == "Consumer row 0"


@pytest.mark.parametrize("surface", ["get", "warning", "all-blocked"])
@pytest.mark.parametrize("anonymous", [False, True], ids=["denied", "anonymous"])
def test_nested_bulk_returns_preserve_request_authorization(
    nested_bulk_return, surface, anonymous, monkeypatch, settings
):
    ns, world, actor, _page, action = nested_bulk_return
    actor.user_permissions.remove(Permission.objects.get(codename="change_book"))
    actor = User.objects.get(pk=actor.pk)
    client = _client(None if anonymous else actor)
    returns = Mock(side_effect=AssertionError("Denied request reached return navigation"))
    monkeypatch.setattr(ns.note.Bulk, "_bulk_back_url", returns)
    if surface == "get":
        response = client.get(action)
    else:
        post = {"cv_bulk_stage": "review"}
        if surface == "all-blocked":
            post["cv_bulk_ids"] = [world.note.pk]
        response = client.post(action, post)
    assert response.status_code == (302 if anonymous else 403)
    if anonymous:
        target = urlsplit(response["Location"])
        assert target.path == settings.LOGIN_URL
        assert parse_qs(target.query) == {"next": [action]}
    else:
        assert "Location" not in response
    returns.assert_not_called()
    assert list(get_messages(response.wsgi_request)) == []
