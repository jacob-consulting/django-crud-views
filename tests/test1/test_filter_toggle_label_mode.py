"""#262: the list filter toggle honours the context label mode (icon, both, label) — Phase 3 / FILT-01..04."""

import logging

import pydantic
import pytest
from django.conf import settings
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import translation
from lxml import html as lxml_html

from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from crud_views.lib.view.base import CrudView
from crud_views.lib.view.buttons import FilterContextButton, context_button_checks
from crud_views.lib.viewset import ViewSet
from tests.lib.helper.icons import HOST_ICONS, HOST_LIBRARY
from tests.test1.app.models import Author
from tests.test1.app.views import AuthorListView, PublisherListView, cv_publisher

FILTER_TOGGLE = "crud_views/tags/context_action_filter.html"

# default icon / class tables: an explicit empty settings layer (setting_changed resets both caches on entry and exit)
default_tables = override_settings(CRUD_VIEWS_ICONS={}, CRUD_VIEWS_ICON_LIBRARIES={}, CRUD_VIEWS_BUTTON_CLASSES={})

RAW_DEFAULT_FILTER = {
    False: (
        "\n"
        '<button type="button"\n'
        '   class="btn btn-outline-primary btn-lg"\n'
        '   id="cv-filter-toggle"\n'
        '   aria-expanded="false"\n'
        '   aria-controls="filter-collapse"\n'
        '   title="Filter"\n'
        '   data-cv-tooltip="context"\n'
        '   cv-key="filter">\n'
        '    <span data-cv-filter-icon="open"><i class="fa-solid fa-filter" aria-hidden="true"></i></span>\n'
        '    <span data-cv-filter-icon="close" hidden>'
        '<i class="fa-solid fa-filter-circle-xmark" aria-hidden="true"></i></span>\n'
        '    <span class="visually-hidden">Filter</span>\n'
        "</button>\n"
    ),
    True: (
        "\n"
        '<button type="button"\n'
        '   class="btn btn-outline-primary btn-lg"\n'
        '   id="cv-filter-toggle"\n'
        '   aria-expanded="true"\n'
        '   aria-controls="filter-collapse"\n'
        '   title="Filter"\n'
        '   data-cv-tooltip="context"\n'
        '   cv-key="filter">\n'
        '    <span data-cv-filter-icon="open" hidden><i class="fa-solid fa-filter" aria-hidden="true"></i></span>\n'
        '    <span data-cv-filter-icon="close">'
        '<i class="fa-solid fa-filter-circle-xmark" aria-hidden="true"></i></span>\n'
        '    <span class="visually-hidden">Filter</span>\n'
        "</button>\n"
    ),
}
"""The exact pre-change render_to_string output of the stock filter toggle, collapsed and expanded.

Captured from the untouched template (source HEAD 3a51f81) and never regenerated. Unlike the normalized toolbar
golden, which sorts attributes and class tokens and collapses whitespace, this is a raw byte comparison: the leading
newline after the load line, the attribute indentation and the trailing newline are protected deliberately, even
though render_snippet() strips the boundary whitespace in page output. A passing golden cannot prove this.
"""


def _render_filter(expanded: bool, mode: str | None = None, **extra) -> str:
    """Render the filter leaf directly; mode None leaves cv_label_mode out of the context (a pre-#262 caller)."""
    ctx = {"cv_filter_expanded": expanded, "cv_action_label": "Filter", "cv_key": "filter", **extra}
    if mode is not None:
        ctx["cv_label_mode"] = mode
    return render_to_string(FILTER_TOGGLE, ctx)


@default_tables
@pytest.mark.parametrize("expanded", [False, True])
def test_filter_raw_default_bytes(expanded):
    with translation.override("en"):
        # a context without cv_label_mode (hand-built, or a pre-#262 override) keeps the exact pre-change output ...
        assert _render_filter(expanded) == RAW_DEFAULT_FILTER[expanded]
        # ... and so does the resolved default mode
        assert _render_filter(expanded, "icon") == RAW_DEFAULT_FILTER[expanded]


# DOM selectors specific to the filter toggle: its icons sit inside data-cv-filter-icon wrapper spans, so the generic
# "an unclassed span is the visible label" predicate of ordinary actions would count those wrappers as labels
VISIBLE_LABEL = "./span[not(@class) and not(@data-cv-filter-icon)]"
WRAPPERS = "./span[@data-cv-filter-icon]"
WRAPPED_ICONS = "./span[@data-cv-filter-icon]//i"


def _filter_node(markup: str):
    """The one filter toggle button in a page or fragment."""
    nodes = lxml_html.fromstring(markup).xpath("//button[@id='cv-filter-toggle']")
    assert len(nodes) == 1, markup
    return nodes[0]


def _publisher_view(client):
    """The rendered publisher list view (the stock page whose toolbar has the filter toggle)."""
    resp = client.get(reverse(cv_publisher.get_router_name("list")))
    assert resp.status_code == 200
    return resp.context["view"]


def _page_toggle(client):
    resp = client.get(reverse(cv_publisher.get_router_name("list")))
    assert resp.status_code == 200
    return _filter_node(resp.content.decode())


def _select_settings_map(monkeypatch, mapping):
    """Select CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE: captured at import, so patch the snapshot, and clear the more
    specific view and ViewSet maps so the setting is the first map found."""
    monkeypatch.setattr(PublisherListView, "cv_context_actions_label_mode", None)
    monkeypatch.setattr(cv_publisher, "context_actions_label_mode", None)
    monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", mapping)


BOTH_CLASSES = {"context:secondary:both": "btn cv-test-both"}


@pytest.mark.django_db
def test_filter_both_tracer(client_user_publisher_view, monkeypatch):
    """A settings-map "both" entry reaches the toggle through the real toolbar and survives the persisted toggle."""
    _select_settings_map(monkeypatch, {"filter": "both"})
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=BOTH_CLASSES):
        # the direct builder context carries the resolved mode
        view = _publisher_view(client_user_publisher_view)
        ctx = FilterContextButton().get_context(view.cv_get_view_context())
        assert ctx.get("cv_label_mode") == "both"

        for expanded in (False, True):
            if expanded:
                post = client_user_publisher_view.post(
                    reverse(cv_publisher.get_router_name("list")),
                    data='{"filter_expanded": true}',
                    content_type="application/json",
                )
                assert post.status_code == 200
            button = _page_toggle(client_user_publisher_view)
            # the both-specific class key reaches the button
            assert button.get("class").split() == ["btn", "cv-test-both"]
            assert button.get("aria-expanded") == str(expanded).lower()
            assert button.get("aria-controls") == "filter-collapse"
            assert button.get("cv-key") == "filter"
            # a visible label: no title and no tooltip marker
            assert button.get("title") is None
            assert button.get("data-cv-tooltip") is None
            labels = button.xpath(VISIBLE_LABEL)
            assert [label.text for label in labels] == ["Filter"]
            assert button.xpath("./span[@class]") == []  # no hidden label next to the visible one
            # element icons: both wrappers, the inactive one hidden
            wrappers = {w.get("data-cv-filter-icon"): w for w in button.xpath(WRAPPERS)}
            assert set(wrappers) == {"open", "close"}
            assert (wrappers["open"].get("hidden") is not None) is expanded
            assert (wrappers["close"].get("hidden") is not None) is not expanded
            assert len(button.xpath(WRAPPED_ICONS)) == 2
            # the label is separated from the icons by whitespace
            assert labels[0].getprevious().tail.strip() == ""
            assert labels[0].getprevious().tail != ""


@pytest.mark.django_db
def test_filter_direct_context_mode_less_icon_class(client_user_publisher_view, monkeypatch):
    """Without a configured mode the direct context resolves the context floor and the leaf keeps icon classes."""
    _select_settings_map(monkeypatch, {})
    view = _publisher_view(client_user_publisher_view)
    assert FilterContextButton().get_context(view.cv_get_view_context()).get("cv_label_mode") == "icon"
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"context:secondary:icon": "btn cv-test-icon"}):
        for expanded in (False, True):
            assert _filter_node(_render_filter(expanded)).get("class").split() == ["btn", "cv-test-icon"]
            assert _filter_node(_render_filter(expanded, "icon")).get("class").split() == ["btn", "cv-test-icon"]


# --- presentation matrix: three modes x two expansion states x four icon placements (D-03 .. D-06) ---

MODES = ["icon", "both", "label"]
MODE_CLASSES = {
    "context:secondary:icon": "btn m-icon",
    "context:secondary:both": "btn m-both",
    "context:secondary:label": "btn m-label",
}
PLACEMENTS = {
    # name: (icon table, open icon host-placed, close icon host-placed)
    "element": ({}, False, False),
    "host": (HOST_ICONS, True, True),
    "open-host-close-element": ({**HOST_ICONS, "filter-close": "fas:xmark"}, True, False),
    "open-element-close-host": ({**HOST_ICONS, "filter": "fas:filter"}, False, True),
}
HOST_CLASS = {"open": "icon-funnel", "close": "icon-x"}


def _placement(name, classes=None):
    icons, _open, _close = PLACEMENTS[name]
    return override_settings(
        CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY,
        CRUD_VIEWS_ICONS=icons,
        CRUD_VIEWS_BUTTON_CLASSES=MODE_CLASSES if classes is None else classes,
    )


def _assert_disclosure(button, expanded: bool, key: str = "filter"):
    """The disclosure contract every mode keeps (D-06, D-10)."""
    assert button.get("type") == "button"
    assert button.get("aria-expanded") == str(expanded).lower()
    assert button.get("aria-controls") == "filter-collapse"
    assert button.get("cv-key") == key


def _assert_label(button, mode: str, label: str = "Filter"):
    """icon: a hidden label plus title and tooltip; both / label: exactly one visible label and neither (D-05)."""
    visible = button.xpath(VISIBLE_LABEL)
    if mode == "icon":
        assert visible == []
        assert [s.text for s in button.xpath("./span[@class='visually-hidden']")] == [label]
        assert button.get("title") == label
        assert button.get("data-cv-tooltip") == "context"
    else:
        assert [v.text_content() for v in visible] == [label]
        assert visible[0].get("data-cv-filter-icon") is None
        assert button.xpath("./span[@class]") == []
        assert button.get("title") is None
        assert button.get("data-cv-tooltip") is None


def _assert_no_icons(button):
    """label mode: no wrapper spans, no descendant icons and no host swap hooks (D-06)."""
    assert button.xpath(WRAPPERS) == []
    assert button.xpath(".//i") == []
    assert button.get("data-cv-filter-icon-open") is None
    assert button.get("data-cv-filter-icon-close") is None


def _assert_icons(button, expanded: bool, host: bool, open_host: bool, close_host: bool):
    if host:
        # both icons host-placed: the active class sits on the button and is swapped there (D-03)
        assert button.xpath(WRAPPERS) == []
        assert button.xpath(".//i") == []
        assert button.get("data-cv-filter-icon-open") == HOST_CLASS["open"]
        assert button.get("data-cv-filter-icon-close") == HOST_CLASS["close"]
        classes = button.get("class").split()
        assert HOST_CLASS["close" if expanded else "open"] in classes
        assert HOST_CLASS["open" if expanded else "close"] not in classes
        return
    # element or mixed placement: two wrapper children, the inactive one hidden, a host icon in its standalone form
    assert button.get("data-cv-filter-icon-open") is None
    assert button.get("data-cv-filter-icon-close") is None
    wrappers = {w.get("data-cv-filter-icon"): w for w in button.xpath(WRAPPERS)}
    assert set(wrappers) == {"open", "close"}
    assert (wrappers["open"].get("hidden") is not None) is expanded
    assert (wrappers["close"].get("hidden") is not None) is not expanded
    for which, is_host in (("open", open_host), ("close", close_host)):
        (icon,) = wrappers[which].xpath(".//i")
        if is_host:
            assert icon.get("class") == f"icon {HOST_CLASS[which]}"
        else:
            assert icon.get("class").startswith("fa-")


@pytest.mark.parametrize("placement", list(PLACEMENTS))
@pytest.mark.parametrize("expanded", [False, True])
@pytest.mark.parametrize("mode", MODES)
def test_filter_mode_placement_matrix(mode, expanded, placement):
    _icons, open_host, close_host = PLACEMENTS[placement]
    with _placement(placement):
        button = _filter_node(_render_filter(expanded, mode))
    _assert_disclosure(button, expanded)
    _assert_label(button, mode)
    classes = button.get("class").split()
    assert classes[:2] == ["btn", f"m-{mode}"]  # the mode's own class key (#209)
    if mode == "label":
        _assert_no_icons(button)
        assert classes == ["btn", "m-label"]
    else:
        _assert_icons(button, expanded, open_host and close_host, open_host, close_host)
    if mode == "both":
        # a literal separator before the visible label, after the icons or the button's opening tag
        label = button.xpath(VISIBLE_LABEL)[0]
        before = label.getprevious().tail if label.getprevious() is not None else button.text
        assert before.endswith(" ")


@pytest.mark.parametrize("slot", [None, ""])
@pytest.mark.parametrize("expanded", [False, True])
@pytest.mark.parametrize("mode", MODES)
def test_filter_host_slot_fallback(mode, expanded, slot):
    """An empty or None context:icon-host slot gives no usable host class: icon / both fall back to the standalone
    child icons, label still renders none (D-03, D-06)."""
    with _placement("host", {**MODE_CLASSES, "context:icon-host": slot}):
        button = _filter_node(_render_filter(expanded, mode))
    _assert_disclosure(button, expanded)
    _assert_label(button, mode)
    if mode == "label":
        _assert_no_icons(button)
    else:
        _assert_icons(button, expanded, False, True, True)
    assert "icon-funnel" not in button.get("class").split()


# --- resolution through the real builder and the authenticated toolbar (D-01, D-02) ---


def _rendered_mode(button) -> str:
    """Which of the three bodies the leaf rendered."""
    if button.get("title") is not None:
        return "icon"
    return "both" if button.xpath(WRAPPERS) else "label"


def _resolve(client, button=None, key="filter"):
    """The mode of the direct builder context and of the toggle in the rendered toolbar."""
    view = _publisher_view(client)
    button = button or view.cv_get_context_button(key)
    direct = button.get_context(view.cv_get_view_context())["cv_label_mode"]
    return direct, _rendered_mode(_page_toggle(client))


def _register_buttons(monkeypatch, *buttons):
    """ViewSet-level buttons; the first button of a key wins, so these shadow the stock filter button."""
    monkeypatch.setattr(cv_publisher, "context_buttons", [*buttons, *cv_publisher.context_buttons])


RESOLUTION = {
    # name: (view map, ViewSet map, settings map, button label_mode, floor, expected)
    "own-view-map-beats-button": ({"filter": "label"}, {"filter": "icon"}, {"filter": "icon"}, "both", None, "label"),
    "button-beats-viewset-map": (None, {"filter": "label"}, {"filter": "icon"}, "both", None, "both"),
    "button-beats-settings-map": (None, None, {"filter": "label"}, "both", None, "both"),
    "viewset-map-beats-settings-map": (None, {"filter": "both"}, {"filter": "label"}, None, None, "both"),
    "settings-map-beats-floor": (None, None, {"filter": "label"}, None, {"context": "both"}, "label"),
    "floor": (None, None, {}, None, {"context": "both"}, "both"),
    "empty-view-map-replaces-lower-maps": ({}, {"filter": "label"}, {"filter": "label"}, None, None, "icon"),
    "unrelated-view-map-replaces-lower-maps": ({"create": "label"}, {"filter": "both"}, {}, None, None, "icon"),
    "empty-viewset-map-replaces-settings-map": (None, {}, {"filter": "label"}, None, {"context": "both"}, "both"),
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", list(RESOLUTION))
def test_filter_mode_resolution(client_user_publisher_view, monkeypatch, case):
    view_map, viewset_map, settings_map, button_mode, floor, expected = RESOLUTION[case]
    monkeypatch.setattr(PublisherListView, "cv_context_actions_label_mode", view_map)
    monkeypatch.setattr(cv_publisher, "context_actions_label_mode", viewset_map)
    monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", settings_map)
    if button_mode is not None:
        _register_buttons(monkeypatch, FilterContextButton(label_mode=button_mode))
    floor_settings = {} if floor is None else {"CRUD_VIEWS_LABEL_MODE_DEFAULTS": floor}
    with override_settings(**floor_settings):
        assert _resolve(client_user_publisher_view) == (expected, expected)


@pytest.mark.django_db
@pytest.mark.parametrize("singular", ["label", "both"])
def test_filter_ignores_list_singular_default(client_user_publisher_view, monkeypatch, singular):
    """The toggle has no target view: the list view's own cv_context_action_label_mode, the default it gives buttons
    targeting it, never reaches the filter (D-01)."""
    _select_settings_map(monkeypatch, {})
    monkeypatch.setattr(PublisherListView, "cv_context_action_label_mode", singular)
    assert _resolve(client_user_publisher_view) == ("icon", "icon")


@pytest.mark.django_db
@pytest.mark.parametrize("mode", MODES)
def test_filter_toolbar_resolves_mode_once(client_user_publisher_view, monkeypatch, mode):
    """The label template and leaf use the same resolution, even if a subclass adds target-view defaults."""
    _select_settings_map(monkeypatch, {})

    class TargetDefaultFilterButton(FilterContextButton):
        def get_context(self, context):
            data = super().get_context(context)
            data["cv_context_label_mode"] = "both"
            return data

    _register_buttons(monkeypatch, TargetDefaultFilterButton(label_template_code="{{ cv_label_mode }}:{{ cv_key }}"))
    resolve = CrudView.cv_get_action_label_mode.__func__
    calls = []

    def counted(cls, location, key, button=None, target_default=None):
        if key == "filter":
            calls.append((location, target_default))
        return resolve(cls, location, key, button, target_default)

    monkeypatch.setattr(CrudView, "cv_get_action_label_mode", classmethod(counted))
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": mode}):
        toggle = _page_toggle(client_user_publisher_view)
    assert calls == [("context", None)]
    _assert_label(toggle, mode, f"{mode}:filter")
    assert _rendered_mode(toggle) == mode


@pytest.mark.django_db
def test_filter_declared_key_and_direct_button(client_user_publisher_view, monkeypatch):
    """A renamed toggle resolves its own key; a direct instance uses its own label_mode, not the registered one."""
    _select_settings_map(monkeypatch, {"search": "label", "filter": "both"})
    search = FilterContextButton(key="search")
    _register_buttons(monkeypatch, search)
    actions = ["search" if key == "filter" else key for key in PublisherListView.cv_context_actions]
    monkeypatch.setattr(PublisherListView, "cv_context_actions", actions)
    view = _publisher_view(client_user_publisher_view)
    ctx = search.get_context(view.cv_get_view_context())
    assert (ctx["cv_key"], ctx["cv_label_mode"]) == ("search", "label")
    toggle = _page_toggle(client_user_publisher_view)
    assert toggle.get("cv-key") == "search"
    assert _rendered_mode(toggle) == "label"

    # direct, unregistered instances: their own label_mode beats the settings map; without one they resolve their
    # declared key through the maps, never the label_mode of the registered button of that key
    _register_buttons(monkeypatch, FilterContextButton(label_mode="label"))
    context = view.cv_get_view_context()
    assert FilterContextButton(label_mode="icon").get_context(context)["cv_label_mode"] == "icon"
    assert FilterContextButton().get_context(context)["cv_label_mode"] == "both"
    assert FilterContextButton(key="search", label_mode="both").get_context(context)["cv_label_mode"] == "both"


@pytest.mark.django_db
def test_filter_live_floor(client_user_publisher_view, monkeypatch):
    """The context floor is read per render: nested overrides apply and restore (Phase 1 lazy floor)."""
    _select_settings_map(monkeypatch, {})
    assert _resolve(client_user_publisher_view) == ("icon", "icon")
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": "both"}):
        assert _resolve(client_user_publisher_view) == ("both", "both")
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": "label"}):
            assert _resolve(client_user_publisher_view) == ("label", "label")
        assert _resolve(client_user_publisher_view) == ("both", "both")
    assert _resolve(client_user_publisher_view) == ("icon", "icon")


# --- customization hooks keep working and see the resolved mode (D-07) ---


def _theme_templates(templates: dict):
    """The test engine with a locmem loader in front, for test-local file templates."""
    engine = dict(settings.TEMPLATES[0])
    options = dict(engine["OPTIONS"])
    options["loaders"] = [
        ("django.template.loaders.locmem.Loader", templates),
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    engine.update(APP_DIRS=False, OPTIONS=options)
    return override_settings(TEMPLATES=[engine])


TEST_TEMPLATES = {
    "t262/label.html": "Search ({{ cv_label_mode }})",
    "t262/button.html": '<b id="cv-filter-toggle" class="custom-file" data-mode="{{ cv_label_mode }}">x</b>',
}
WHOLE_CODE = '<b id="cv-filter-toggle" class="custom-code" data-mode="{{ cv_label_mode }}">{{ cv_action_label }}</b>'


@pytest.mark.django_db
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize(
    "label",
    [{"label_template": "t262/label.html"}, {"label_template_code": "Search ({{ cv_label_mode }})"}],
    ids=["label_template", "label_template_code"],
)
def test_filter_custom_label(client_user_publisher_view, monkeypatch, mode, label):
    _select_settings_map(monkeypatch, {"filter": mode})
    _register_buttons(monkeypatch, FilterContextButton(**label))
    with _theme_templates(TEST_TEMPLATES):
        toggle = _page_toggle(client_user_publisher_view)
    assert _rendered_mode(toggle) == mode
    text = f"Search ({mode})"  # the custom label saw the resolved mode
    if mode == "icon":
        assert toggle.get("title") == text
        assert toggle.xpath("./span[@class='visually-hidden']")[0].text == text
    else:
        assert [s.text for s in toggle.xpath(VISIBLE_LABEL)] == [text]


@pytest.mark.django_db
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize(
    ("hook", "marker"),
    [
        ({"template": "t262/button.html"}, "custom-file"),
        ({"template_code": WHOLE_CODE}, "custom-code"),
        ({"template": "t262/button.html", "template_code": WHOLE_CODE}, "custom-code"),  # template_code first
    ],
    ids=["template", "template_code", "template_code-beats-template"],
)
def test_filter_whole_button_template(client_user_publisher_view, monkeypatch, mode, hook, marker):
    _select_settings_map(monkeypatch, {"filter": mode})
    _register_buttons(monkeypatch, FilterContextButton(**hook))
    with _theme_templates(TEST_TEMPLATES):
        resp = client_user_publisher_view.get(reverse(cv_publisher.get_router_name("list")))
    (toggle,) = lxml_html.fromstring(resp.content).xpath("//*[@id='cv-filter-toggle']")
    assert toggle.tag == "b"
    assert toggle.get("class") == marker  # owns its markup: no stock classes, icons or labels
    assert toggle.get("data-mode") == mode


@pytest.mark.django_db
@pytest.mark.parametrize("mode", MODES)
def test_filter_variant_mode_classes(client_user_publisher_view, monkeypatch, mode):
    _select_settings_map(monkeypatch, {"filter": mode})
    _register_buttons(monkeypatch, FilterContextButton(variant="primary"))
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={f"context:primary:{mode}": f"btn v-primary-{mode}"}):
        toggle = _page_toggle(client_user_publisher_view)
    assert toggle.get("class").split() == ["btn", f"v-primary-{mode}"]


@pytest.mark.django_db
def test_filter_customization(client_user_publisher_view, monkeypatch):
    """An empty custom label result keeps the seeded default; the label template sees the resolved mode."""
    _select_settings_map(monkeypatch, {"filter": "label"})
    view = _publisher_view(client_user_publisher_view)
    context = view.cv_get_view_context()
    empty = FilterContextButton(label_template_code="{% if cv_label_mode == 'icon' %}never{% endif %}")
    assert empty.get_context(context)["cv_action_label"] == "Filter"
    seen = FilterContextButton(label_template_code="{{ cv_label_mode }}:{{ cv_key }}")
    assert seen.get_context(context)["cv_action_label"] == "label:filter"
    _register_buttons(monkeypatch, empty)
    toggle = _page_toggle(client_user_publisher_view)
    assert [s.text for s in toggle.xpath(VISIBLE_LABEL)] == ["Filter"]


# --- visibility is unchanged (D-10) ---


@pytest.mark.django_db
def test_filter_visibility(client_user_publisher_view, user_author_view, monkeypatch):
    _select_settings_map(monkeypatch, {"filter": "both"})
    # a list without a filter: no toggle, and no mode is resolved or stamped
    author_client = Client()  # its own client: the client_user_* fixtures share one and the last login wins
    author_client.force_login(user_author_view)
    resp = author_client.get(reverse(AuthorListView.cv_viewset.get_router_name("list")))
    assert resp.status_code == 200
    assert lxml_html.fromstring(resp.content).xpath("//*[@id='cv-filter-toggle']") == []
    assert FilterContextButton().get_context(resp.context["view"].cv_get_view_context()) == {"cv_access": False}
    # a pinned filter: always shown, no toggle
    monkeypatch.setattr(PublisherListView, "cv_filter_pinned", True)
    resp = client_user_publisher_view.get(reverse(cv_publisher.get_router_name("list")))
    assert lxml_html.fromstring(resp.content).xpath("//*[@id='cv-filter-toggle']") == []
    assert FilterContextButton().get_context(resp.context["view"].cv_get_view_context()) == {"cv_access": False}


# --- ordinary labels are escaped, the trusted-template boundary is unchanged (T-03-01) ---


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("label", ['<b onclick="x()">Fïltér & «Ω»</b>', "Filtrer ✓"])
def test_filter_label_escaping(mode, label):
    with default_tables:
        markup = _render_filter(False, mode, cv_action_label=label)
    button = _filter_node(markup)
    assert button.xpath(".//b") == []
    assert "<b " not in markup
    _assert_label(button, mode, label)


# --- compatibility fallback for direct contexts and the existing invalid-configuration policy (A1, C2-A1) ---


@pytest.mark.parametrize("expanded", [False, True])
@pytest.mark.parametrize("value", ["absent", None, "", "text"])
def test_filter_direct_mode_fallback(value, expanded):
    """A direct context without a supported mode renders the legacy icon body and icon classes, whatever the floor.

    The leaf does not resolve configuration: only its explicit both / label branches leave the icon form.
    """
    extra = {} if value == "absent" else {"cv_label_mode": value}
    classes = {"context:secondary:icon": "btn m-icon", "context:secondary:both": "btn m-both"}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=classes, CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": "both"}):
        button = _filter_node(_render_filter(expanded, **extra))
    assert button.get("class").split() == ["btn", "m-icon"]
    _assert_disclosure(button, expanded)
    _assert_label(button, "icon")
    _assert_icons(button, expanded, False, False, False)
    with default_tables:
        assert _render_filter(expanded, **extra) == RAW_DEFAULT_FILTER[expanded]


def _check_ids(checks) -> list[str]:
    return [m.id for c in checks for m in c.messages()]


@pytest.mark.django_db
def test_filter_invalid_configuration_policy(client_user_publisher_view, monkeypatch, caplog):
    """Malformed configuration is diagnosed by the existing checks; this phase adds no runtime normalizer.

    Four separate paths: a button label_mode (viewset.E210), the view's own map (viewset.E211), the settings map
    (crud_views.E106) and a ViewSet map, which pydantic rejects at construction. A malformed map or button value that
    still reaches rendering is returned raw by the resolver and the stock leaf renders its legacy icon form; that is a
    limitation, not a supported configuration. An invalid floor keeps its strict / warn-once policy.
    """
    bogus = FilterContextButton(label_mode="text")
    assert _check_ids(context_button_checks(PublisherListView, cv_publisher, [bogus])) == ["viewset.E210"]

    with monkeypatch.context() as mp:
        mp.setattr(PublisherListView, "cv_context_actions_label_mode", {"filter": "text"})
        assert "viewset.E211" in _check_ids(PublisherListView.checks())
    assert "viewset.E211" not in _check_ids(PublisherListView.checks())

    messages = CrudViewsSettings(context_actions_label_mode={"filter": "text"}).check_messages
    assert [m.id for m in messages] == ["crud_views.E106"]

    with pytest.raises(pydantic.ValidationError):
        ViewSet(model=Author, name="author_bad_filter_map_262", context_actions_label_mode={"filter": "text"})

    # the unvalidated raw value reaches the leaf, which renders the legacy icon form
    _select_settings_map(monkeypatch, {"filter": "text"})
    view = _publisher_view(client_user_publisher_view)
    assert FilterContextButton().get_context(view.cv_get_view_context())["cv_label_mode"] == "text"
    assert _rendered_mode(_page_toggle(client_user_publisher_view)) == "icon"

    # an invalid floor reached with nothing named before it: strict raises, non-strict warns once and uses "icon"
    _select_settings_map(monkeypatch, {})
    context = view.cv_get_view_context()
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": "Both"}):
        with pytest.raises(ValueError, match="CRUD_VIEWS_LABEL_MODE_DEFAULTS"):
            FilterContextButton().get_context(context)
        # a valid explicit mode short-circuits the floor
        assert FilterContextButton(label_mode="label").get_context(context)["cv_label_mode"] == "label"
        with override_settings(CRUD_VIEWS_STRICT=False), caplog.at_level(logging.WARNING):
            assert FilterContextButton().get_context(context)["cv_label_mode"] == "icon"
            assert FilterContextButton().get_context(context)["cv_label_mode"] == "icon"
    warnings = [r for r in caplog.records if r.name == "crud_views.lib.view.label_mode"]
    assert len(warnings) == 1
