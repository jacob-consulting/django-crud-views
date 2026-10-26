import pytest
from django.contrib.auth.models import User
from django.contrib.messages import constants, get_messages
from django.contrib.messages.storage.base import Message
from django.template import Context, Template
from django.test.client import Client
from django.utils.safestring import mark_safe

from crud_views.lib.messages import message_alerts
from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def client_publisher_add_view(client, cv_publisher) -> Client:
    """Client with both add and view permissions (needed to follow redirect to list)."""
    user = User.objects.create_user(username="user_pub_add_view", password="password")
    user_viewset_permission(user, cv_publisher, "add")
    user_viewset_permission(user, cv_publisher, "view")
    client.force_login(user)
    return client


@pytest.fixture
def client_publisher_change_view(client, cv_publisher) -> Client:
    """Client with both change and view permissions."""
    user = User.objects.create_user(username="user_pub_change_view", password="password")
    user_viewset_permission(user, cv_publisher, "change")
    user_viewset_permission(user, cv_publisher, "view")
    client.force_login(user)
    return client


@pytest.fixture
def client_publisher_delete_view(client, cv_publisher) -> Client:
    """Client with both delete and view permissions."""
    user = User.objects.create_user(username="user_pub_delete_view", password="password")
    user_viewset_permission(user, cv_publisher, "delete")
    user_viewset_permission(user, cv_publisher, "view")
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_create_message(client_publisher_add_view: Client, cv_publisher):
    response = client_publisher_add_view.post("/publisher/create/", {"name": "Penguin"}, follow=True)
    assert response.status_code == 200

    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert "Created" in str(messages[0])
    assert "Penguin" in str(messages[0])


@pytest.mark.django_db
def test_update_message(client_publisher_change_view: Client, cv_publisher, publisher_penguin):
    pk = publisher_penguin.pk
    response = client_publisher_change_view.post(f"/publisher/{pk}/update/", {"name": "Penguin Classics"}, follow=True)
    assert response.status_code == 200

    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert "Updated" in str(messages[0])
    assert "Penguin Classics" in str(messages[0])


@pytest.mark.django_db
def test_delete_message(client_publisher_delete_view: Client, cv_publisher, publisher_penguin):
    pk = publisher_penguin.pk
    response = client_publisher_delete_view.post(f"/publisher/{pk}/delete/", {"confirm": True}, follow=True)
    assert response.status_code == 200

    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert "Deleted" in str(messages[0])
    assert "Penguin" in str(messages[0])


@pytest.mark.django_db
def test_no_message_on_get(client_user_publisher_view: Client, cv_publisher, publisher_penguin):
    """GET requests should not produce any flash messages."""
    pk = publisher_penguin.pk
    response = client_user_publisher_view.get(f"/publisher/{pk}/detail/")
    assert response.status_code == 200

    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 0


@pytest.mark.parametrize(
    "level,alert_level,icon_name",
    [
        (constants.DEBUG, "debug", "message-debug"),
        (constants.INFO, "info", "message-info"),
        (constants.SUCCESS, "success", "message-success"),
        (constants.WARNING, "warning", "message-warning"),
        (constants.ERROR, "error", "message-error"),
    ],
)
def test_message_alerts_maps_every_level(level, alert_level, icon_name):
    (alert,) = message_alerts([Message(level, "hello")])
    assert alert["text"] == "hello"
    assert alert["level"] == alert_level
    assert alert["icon_name"] == icon_name
    assert alert["extra_tags"] == ""
    assert alert["dismissible"] is True


def test_message_alerts_keeps_extra_tags():
    (alert,) = message_alerts([Message(constants.INFO, "hello", extra_tags="mb-0 shadow")])
    assert alert["extra_tags"] == "mb-0 shadow"


def test_message_alerts_falls_back_to_info_for_unknown_level():
    (alert,) = message_alerts([Message(50, "hello")])
    assert alert["level"] == "info"
    assert alert["icon_name"] == "message-info"


def test_message_alerts_falls_back_to_info_without_a_level():
    (alert,) = message_alerts(["a plain string"])
    assert alert["text"] == "a plain string"
    assert alert["level"] == "info"


@pytest.mark.parametrize("messages", [None, []])
def test_message_alerts_without_messages(messages):
    assert message_alerts(messages) == []


def _render(messages):
    return Template("{% load crud_views %}{% cv_messages %}").render(Context({"messages": messages}))


def test_cv_messages_renders_a_dismissible_alert():
    html = _render([Message(constants.SUCCESS, "Saved")])
    assert 'class="alert alert-success alert-dismissible fade show"' in html
    assert 'role="alert"' in html
    assert '<i class="fa-solid fa-circle-check' in html
    assert "data-cv-alert-dismiss" in html
    assert 'class="btn-close"' in html
    assert "Saved" in html


def test_cv_messages_appends_extra_tags_to_the_class_list():
    html = _render([Message(constants.INFO, "Note", extra_tags="mb-0")])
    assert 'class="alert alert-info alert-dismissible fade show mb-0"' in html


def test_cv_messages_keeps_safe_markup_unescaped():
    html = _render([Message(constants.SUCCESS, mark_safe("Created <strong>Penguin</strong>"))])
    assert "Created <strong>Penguin</strong>" in html


def test_cv_messages_escapes_unsafe_markup():
    html = _render([Message(constants.ERROR, "<script>x</script>")])
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html


def test_cv_messages_renders_nothing_without_messages_in_the_context():
    assert Template("{% load crud_views %}{% cv_messages %}").render(Context({})).strip() == ""


@pytest.mark.django_db
def test_create_message_renders_as_an_alert(client_publisher_add_view: Client, cv_publisher):
    response = client_publisher_add_view.post("/publisher/create/", {"name": "Penguin"}, follow=True)
    html = response.content.decode()
    assert 'class="alert alert-success alert-dismissible fade show"' in html
    assert "data-cv-alert-dismiss" in html
    assert "<strong>Penguin</strong>" in html


def test_cv_messages_escapes_even_with_autoescape_off():
    """The replaced library built alerts with format_html, which escapes unconditionally; keep that guarantee."""
    template = Template("{% load crud_views %}{% autoescape off %}{% cv_messages %}{% endautoescape %}")
    html = template.render(Context({"messages": [Message(constants.ERROR, "<script>x</script>", extra_tags='">')]}))
    assert "<script>x</script>" not in html
    assert '<div class="alert alert-danger alert-dismissible fade show &quot;&gt;"' in html


@pytest.mark.parametrize("body", [None, ""])
def test_message_alerts_blanks_a_falsy_body(body):
    """The replaced tag rendered `message.message|default:""`, i.e. an empty alert rather than the text "None".

    Only reachable without a storage round-trip: Message._prepare() str()s the body, so after a redirect a None
    body has already become the string "None" before it reaches us.
    """
    (alert,) = message_alerts([Message(constants.INFO, body)])
    assert alert["text"] == ""
