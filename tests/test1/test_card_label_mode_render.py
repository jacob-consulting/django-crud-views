"""#213: the three label modes as rendered by crud_views/tags/button/action.html on card buttons."""

import uuid
import warnings

import pytest
from django.contrib.auth.models import User
from django.test import Client, RequestFactory, override_settings
from django.urls import resolve, reverse
from lxml import html as lxml_html

from crud_views.lib.view import CardAction
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import (
    AuthorCardListView,
    AuthorPingView,
    AuthorUpdateView,
    PublisherCardListView,
    cv_author,
    cv_book,
    cv_publisher,
)

CARD = "//div[contains(@class, 'card') and contains(@class, 'mb-3')]"
AUTHOR_FULL = (cv_author, ("view", "add", "change", "delete"))
AUTHOR_VIEW_ONLY = (cv_author, ("view",))


def _client(grants) -> Client:
    user = User.objects.create_user(username=f"card_213_{uuid.uuid4().hex[:8]}", password="pw")
    for viewset, perms in grants:
        for perm in perms:
            user_viewset_permission(user, viewset, perm)
    client = Client()
    client.force_login(user)
    return client


def _card(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    return lxml_html.fromstring(resp.content).xpath(CARD)[0]


def _render_card_view(view_class, user, *, initkwargs=None, query=None):
    """Render an actual card response, including action groups and the button leaf."""
    url = reverse(view_class.cv_viewset.get_router_name("card"))
    request = RequestFactory().get(url, data=query or {})
    request.user = user
    request.resolver_match = resolve(url)
    response = view_class.as_view(**(initkwargs or {}))(request)
    assert response.status_code == 200
    response.render()
    (card,) = lxml_html.fromstring(response.content).xpath(CARD)
    return card


def _inline(card, key):
    """The one inline card button for a CardAction key (or child_name)."""
    (button,) = card.xpath(f'.//*[@cv-card-container]/*[@cv-key="{key}"]')
    return button


def _icons(button) -> list:
    return button.xpath(".//i")


def _text(button) -> str:
    return button.text_content().strip()


def _markup(button) -> str:
    return lxml_html.tostring(button, encoding="unicode")


def _author_card(client, actions, monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", actions)
    return _card(client, reverse(cv_author.get_router_name("card")))


@pytest.mark.django_db
def test_three_states_on_one_card(author_douglas_adams, monkeypatch):
    card = _author_card(
        _client([AUTHOR_FULL]),
        [
            CardAction(key="detail", label="Details", label_mode="both"),
            CardAction(key="update", label="Edit", label_mode="label"),
            CardAction(key="delete", label="Delete", label_mode="icon"),
        ],
        monkeypatch,
    )

    both = _inline(card, "detail")
    assert len(_icons(both)) == 1
    # the visible span is the only accessible name: the icon is hidden, and nothing duplicates or overrides it
    assert all(i.get("aria-hidden") == "true" for i in _icons(both))
    assert _text(both) == "Details"
    assert both.cssselect("span.visually-hidden") == []
    assert both.get("aria-label") is None
    assert both.get("title") is None
    # the literal space between glyph and text is invisible to the whitespace-normalising goldens
    assert _icons(both)[0].tail == " "

    label = _inline(card, "update")
    assert _icons(label) == []
    assert _text(label) == "Edit"
    assert label.cssselect("span.visually-hidden") == []
    assert label.get("title") is None

    icon = _inline(card, "delete")
    assert len(_icons(icon)) == 1
    (hidden,) = icon.cssselect("span.visually-hidden")
    assert hidden.text_content().strip() == "Delete"
    assert icon.get("title") == "Delete"


@pytest.mark.django_db
def test_no_label_still_means_icon_only(author_douglas_adams, monkeypatch):
    client = _client([AUTHOR_FULL])
    legacy = _inline(
        _author_card(client, [CardAction(key="delete", label="Delete", no_label=True)], monkeypatch), "delete"
    )
    explicit = _inline(
        _author_card(client, [CardAction(key="delete", label="Delete", label_mode="icon")], monkeypatch), "delete"
    )

    assert len(_icons(legacy)) == 1
    assert legacy.cssselect("span.visually-hidden")[0].text_content().strip() == "Delete"
    assert legacy.get("title") == "Delete"
    assert _markup(legacy) == _markup(explicit)


@pytest.mark.django_db
def test_view_default_applies_and_action_overrides_it(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_label_mode", "label")
    card = _author_card(
        _client([AUTHOR_FULL]),
        [
            CardAction(key="detail", label="Details"),
            CardAction(key="update", label="Edit", label_mode="both"),
        ],
        monkeypatch,
    )

    inherited = _inline(card, "detail")
    assert _icons(inherited) == []
    assert _text(inherited) == "Details"

    override = _inline(card, "update")
    assert len(_icons(override)) == 1
    assert _text(override) == "Edit"


@pytest.mark.django_db
def test_both_without_an_icon_renders_label_only(author_douglas_adams, monkeypatch):
    # ActionView leaves cv_icon_action unset, but pin it so the iconless case is arranged, not inherited
    monkeypatch.setattr(AuthorPingView, "cv_icon_action", None)
    client = _client([AUTHOR_FULL])

    both = _inline(_author_card(client, [CardAction(key="ping", label="Ping", label_mode="both")], monkeypatch), "ping")
    assert _icons(both) == []
    assert _text(both) == "Ping"

    label = _inline(
        _author_card(client, [CardAction(key="ping", label="Ping", label_mode="label")], monkeypatch), "ping"
    )
    assert _markup(both) == _markup(label)


@pytest.mark.django_db
def test_child_name_card_action_resolves_label_mode(publisher_penguin, monkeypatch):
    client = _client([(cv_publisher, ("view",)), (cv_book, ("view",))])
    url = reverse(cv_publisher.get_router_name("card"))

    def books(label_mode):
        action = CardAction(child_name="book", child_key="list", label="Books", label_mode=label_mode)
        monkeypatch.setattr(PublisherCardListView, "cv_card_actions", [action])
        return _inline(_card(client, url), "book")

    # a non-default mode: the child branch has to resolve it, the "both" fallback cannot supply it
    label = books("label")
    assert _icons(label) == []
    assert _text(label) == "Books"

    both = books("both")
    assert len(_icons(both)) == 1
    assert _text(both) == "Books"


@pytest.mark.django_db
def test_disabled_card_action_in_both_mode(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    card = _author_card(
        _client([AUTHOR_VIEW_ONLY]), [CardAction(key="update", label="Edit", label_mode="both")], monkeypatch
    )

    button = _inline(card, "update")
    assert button.tag == "button"
    assert button.get("disabled") is not None
    assert button.get("data-cv-disabled") == "permission"
    assert button.get("href") is None
    assert len(_icons(button)) == 1
    assert _text(button) == "Edit"


@pytest.mark.django_db
def test_post_only_card_action_in_both_mode(author_douglas_adams, monkeypatch):
    card = _author_card(_client([AUTHOR_FULL]), [CardAction(key="up", label="Up", label_mode="both")], monkeypatch)

    button = _inline(card, "up")
    assert button.tag == "button"
    assert button.get("data-cv-action") == "submit-form"
    assert button.get("href") is None
    assert len(_icons(button)) == 1
    assert _text(button) == "Up"


@pytest.mark.django_db
def test_menu_item_ignores_label_mode(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", ["detail"])
    card = _author_card(
        _client([AUTHOR_FULL]),
        [
            CardAction(key="detail", label="Details"),
            CardAction(key="delete", label="Delete", label_mode="icon"),
        ],
        monkeypatch,
    )

    (item,) = card.cssselect(".dropdown-item")
    assert item.get("cv-key") == "delete"
    assert len(_icons(item)) == 1
    assert _text(item) == "Delete"
    assert item.cssselect("span.visually-hidden") == []
    assert item.get("title") is None


CARD_LABEL = {"card": "label"}


def _assert_label_only(button, text):
    assert _text(button) == text
    assert _icons(button) == []
    assert button.cssselect("span.visually-hidden") == []
    assert button.get("title") is None


def _assert_icon_only(button):
    assert len(_icons(button)) == 1
    (hidden,) = button.cssselect("span.visually-hidden")
    label = hidden.text_content().strip()
    assert label
    assert button.get("title") == label


def _assert_both(button, text):
    assert len(_icons(button)) == 1
    assert _icons(button)[0].get("aria-hidden") == "true"
    assert _text(button) == text
    assert button.cssselect("span.visually-hidden") == []
    assert button.get("aria-label") is None
    assert button.get("title") is None


@pytest.mark.django_db
def test_card_initkwargs_label_without_setting(author_douglas_adams, user_author_view, settings):
    if hasattr(settings, "CRUD_VIEWS_LABEL_MODE_DEFAULTS"):
        del settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS
    assert not hasattr(settings, "CRUD_VIEWS_LABEL_MODE_DEFAULTS")

    label = _inline(
        _render_card_view(AuthorCardListView, user_author_view, initkwargs={"cv_card_actions_label_mode": "label"}),
        "detail",
    )
    _assert_label_only(label, "Details")

    control = _inline(_render_card_view(AuthorCardListView, user_author_view), "detail")
    assert len(_icons(control)) == 1
    assert _icons(control)[0].get("aria-hidden") == "true"
    assert _text(control) == "Details"
    assert control.cssselect("span.visually-hidden") == []
    assert control.get("title") is None


@pytest.mark.django_db
@pytest.mark.parametrize("entry", ["initkwargs", "setup"])
@pytest.mark.parametrize("floor, mode", [(None, "label"), ("label", "both"), ("invalid", "both")])
def test_card_instance_mode_precedence(author_douglas_adams, user_author_view, settings, entry, floor, mode):
    if hasattr(settings, "CRUD_VIEWS_LABEL_MODE_DEFAULTS"):
        del settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS
    if floor is not None:
        settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": floor}
    else:
        assert not hasattr(settings, "CRUD_VIEWS_LABEL_MODE_DEFAULTS")
    settings.CRUD_VIEWS_STRICT = True
    for permission in ("change", "delete"):
        user_viewset_permission(user_author_view, cv_author, permission)

    # Defensive action-mode precedence even if a caller bypasses CardAction's validation.
    explicit = CardAction(key="delete", label="Delete", no_label=True)
    object.__setattr__(explicit, "label_mode", "both" if mode == "label" else "label")

    class InstanceView(AuthorCardListView):
        cv_card_actions = [
            CardAction(key="detail", label="Details"),
            CardAction(key="update", label="Edit", label_mode="icon"),
            explicit,
            CardAction(key="up", label="Up", no_label=True),
        ]

        def setup(self, request, *args, **kwargs):
            super().setup(request, *args, **kwargs)
            if entry == "setup":
                self.cv_card_actions_label_mode = mode

    initkwargs = {"cv_card_actions_label_mode": mode} if entry == "initkwargs" else {}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        card = _render_card_view(InstanceView, user_author_view, initkwargs=initkwargs)
    assert [w for w in caught if issubclass(w.category, DeprecationWarning)] == []
    (_assert_label_only if mode == "label" else _assert_both)(_inline(card, "detail"), "Details")
    _assert_icon_only(_inline(card, "update"))
    (_assert_both if mode == "label" else _assert_label_only)(_inline(card, "delete"), "Delete")
    _assert_icon_only(_inline(card, "up"))
    assert InstanceView.cv_card_actions_label_mode is None


@pytest.mark.django_db
@pytest.mark.parametrize("hook", ["setup", "dispatch", "get_queryset"])
@pytest.mark.parametrize("floor", [None, "label"])
def test_card_request_assignment_is_local(author_douglas_adams, user_author_view, settings, hook, floor):
    if hasattr(settings, "CRUD_VIEWS_LABEL_MODE_DEFAULTS"):
        del settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS
    if floor is not None:
        settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": floor}
    else:
        assert not hasattr(settings, "CRUD_VIEWS_LABEL_MODE_DEFAULTS")

    class RequestView(AuthorCardListView):
        def setup(self, request, *args, **kwargs):
            super().setup(request, *args, **kwargs)
            if hook == "setup" and "mode" in request.GET:
                self.cv_card_actions_label_mode = request.GET["mode"]

        def dispatch(self, request, *args, **kwargs):
            if hook == "dispatch" and "mode" in request.GET:
                self.cv_card_actions_label_mode = request.GET["mode"]
            return super().dispatch(request, *args, **kwargs)

        def get_queryset(self):
            if hook == "get_queryset" and "mode" in self.request.GET:
                self.cv_card_actions_label_mode = self.request.GET["mode"]
            return super().get_queryset()

    for requested, expected in [("label", "label"), ("both", "both"), (None, floor or "both")]:
        query = {"mode": requested} if requested is not None else {}
        card = _render_card_view(RequestView, user_author_view, query=query)
        (_assert_label_only if expected == "label" else _assert_both)(_inline(card, "detail"), "Details")
        assert RequestView.cv_card_actions_label_mode is None
        assert AuthorCardListView.cv_card_actions_label_mode is None


@pytest.mark.django_db
@pytest.mark.parametrize("class_mode", ["label", "both"])
def test_card_instance_none_uses_floor(author_douglas_adams, user_author_view, class_mode):
    instances = []

    class ResetView(AuthorCardListView):
        cv_card_actions_label_mode = class_mode

        def setup(self, request, *args, **kwargs):
            super().setup(request, *args, **kwargs)
            instances.append(self)

    floor = "both" if class_mode == "label" else "label"
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": floor}):
        inherited = _render_card_view(ResetView, user_author_view)
        (_assert_label_only if class_mode == "label" else _assert_both)(_inline(inherited, "detail"), "Details")
        card = _render_card_view(ResetView, user_author_view, initkwargs={"cv_card_actions_label_mode": None})
        (_assert_label_only if floor == "label" else _assert_both)(_inline(card, "detail"), "Details")
        instance = instances[-1]
        assert "cv_card_actions_label_mode" in vars(instance)
        assert instance.cv_card_actions_label_mode is None

        def assert_current(expected):
            data = instance.cv_get_card_action_data(instance.cv_card_actions[0], author_douglas_adams, user_author_view)
            assert data["cv_label_mode"] == expected
            response = instance.get(instance.request)
            response.render()
            (current_card,) = lxml_html.fromstring(response.content).xpath(CARD)
            (_assert_label_only if expected == "label" else _assert_both)(_inline(current_card, "detail"), "Details")

        assert_current(floor)
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": class_mode}):
            assert_current(class_mode)
        assert_current(floor)
        # Clearing an instance override changes neither the class nor a subsequent request.
        instance.cv_card_actions_label_mode = "icon"
        instance.cv_card_actions_label_mode = None
        assert_current(floor)
        later = _render_card_view(ResetView, user_author_view)
        (_assert_label_only if class_mode == "label" else _assert_both)(_inline(later, "detail"), "Details")
    assert ResetView.cv_card_actions_label_mode == class_mode


@pytest.mark.django_db
@pytest.mark.parametrize("resolver", ["classmethod", "instance"])
def test_card_resolver_hook_reaches_render(author_douglas_adams, user_author_view, resolver):
    class ClassHookView(AuthorCardListView):
        cv_card_actions_label_mode = "both"

        @classmethod
        def cv_get_card_actions_label_mode(cls):
            assert super().cv_get_card_actions_label_mode() == "both"
            return "label"

    class InstanceHookView(AuthorCardListView):
        cv_card_actions_label_mode = "both"

        def cv_get_card_actions_label_mode(self):
            assert super().cv_get_card_actions_label_mode() == "both"
            return self.request.GET["fallback"]

    view_class = ClassHookView if resolver == "classmethod" else InstanceHookView
    if resolver == "classmethod":
        assert view_class.cv_get_card_actions_label_mode() == "label"
    card = _render_card_view(view_class, user_author_view, query={"fallback": "label"})
    _assert_label_only(_inline(card, "detail"), "Details")
    explicit = _render_card_view(
        view_class,
        user_author_view,
        initkwargs={"cv_card_actions_label_mode": "both"},
        query={"fallback": "label"},
    )
    _assert_both(_inline(explicit, "detail"), "Details")


@pytest.mark.django_db
@pytest.mark.parametrize("book_access", [True, False])
def test_card_instance_mode_reaches_child_action(publisher_penguin, user_author_view, book_access):
    user_viewset_permission(user_author_view, cv_publisher, "view")
    if book_access:
        user_viewset_permission(user_author_view, cv_book, "view")
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "both"}):
        card = _render_card_view(
            PublisherCardListView, user_author_view, initkwargs={"cv_card_actions_label_mode": "label"}
        )
    _assert_label_only(_inline(card, "detail"), "Details")
    if book_access:
        _assert_label_only(_inline(card, "book"), "Books")
    else:
        assert card.xpath('.//*[@cv-key="book"]') == []


@pytest.mark.django_db
def test_card_floor_renders_label_only(author_douglas_adams):
    # the stock AuthorCardListView, no attribute or action-list change: the project setting alone (LMOD-03)
    client = _client([AUTHOR_FULL])
    url = reverse(cv_author.get_router_name("card"))
    with warnings.catch_warnings(record=True) as caught, override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=CARD_LABEL):
        warnings.simplefilter("always")
        card = _card(client, url)

    _assert_label_only(_inline(card, "detail"), "Details")
    _assert_label_only(_inline(card, "update"), "Edit")
    # the stock delete action keeps no_label=True, which still means icon-only with an accessible name (D-18)
    _assert_icon_only(_inline(card, "delete"))
    assert [w for w in caught if issubclass(w.category, DeprecationWarning)] == []


@pytest.mark.django_db
def test_card_mode_precedence_with_floor(author_douglas_adams, monkeypatch):
    client = _client([AUTHOR_FULL])
    # CardAction validates at construction, so bypass the validator to model label_mode alongside no_label
    explicit_over_no_label = CardAction(key="delete", label="Delete", no_label=True)
    object.__setattr__(explicit_over_no_label, "label_mode", "label")
    actions = [
        CardAction(key="detail", label="Details"),
        CardAction(key="update", label="Edit", label_mode="both"),
        explicit_over_no_label,
        CardAction(key="up", label="Up", no_label=True),
    ]

    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=CARD_LABEL):
        card = _author_card(client, actions, monkeypatch)
    # unset action: the card floor; explicit action mode wins over the floor and over no_label
    _assert_label_only(_inline(card, "detail"), "Details")
    update = _inline(card, "update")
    assert len(_icons(update)) == 1
    assert _text(update) == "Edit"
    _assert_label_only(_inline(card, "delete"), "Delete")
    # no_label beats the floor
    _assert_icon_only(_inline(card, "up"))

    # an explicitly assigned view attribute beats the floor; no_label still beats the view attribute
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_label_mode", "both")
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=CARD_LABEL):
        card = _author_card(client, actions, monkeypatch)
    detail = _inline(card, "detail")
    assert len(_icons(detail)) == 1
    assert _text(detail) == "Details"
    _assert_icon_only(_inline(card, "up"))


@pytest.mark.django_db
def test_empty_card_actions_with_floor(author_douglas_adams, monkeypatch):
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=CARD_LABEL):
        card = _author_card(_client([AUTHOR_FULL]), [], monkeypatch)
    # no default button is invented
    assert card.xpath(".//*[@cv-key]") == []
    assert card.xpath(".//a | .//button") == []


@pytest.mark.django_db
def test_context_override_keeps_card_action_body(author_douglas_adams):
    # a context/list floor may change the page toolbar, but never the card action body
    client = _client([AUTHOR_FULL])
    url = reverse(cv_author.get_router_name("card"))
    baseline = _markup(_card(client, url))
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": "both", "list": "label"}):
        overridden = _markup(_card(client, url))
    assert overridden == baseline
