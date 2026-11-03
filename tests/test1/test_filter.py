import pytest
from django.test.client import Client

from tests.lib.helper.boostrap5 import Table


@pytest.mark.django_db
def test_filter_no_params_shows_all(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, publisher_harpercollins
):
    """Without filter params, all publishers are listed."""
    response = client_user_publisher_view.get("/publisher/")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 2


@pytest.mark.django_db
def test_filter_by_name_match(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, publisher_harpercollins
):
    """Filter with matching name returns only the matched publisher."""
    response = client_user_publisher_view.get("/publisher/?name=penguin")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 1
    assert "Penguin" in table.rows[0].columns[1].text


@pytest.mark.django_db
def test_filter_by_name_no_match(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, publisher_harpercollins
):
    """Filter with non-matching name returns empty table."""
    response = client_user_publisher_view.get("/publisher/?name=nonexistent")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 0


@pytest.mark.django_db
def test_filter_is_case_insensitive(client_user_publisher_view: Client, cv_publisher, publisher_penguin):
    """icontains lookup should be case-insensitive."""
    response = client_user_publisher_view.get("/publisher/?name=PENGUIN")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 1
    assert "Penguin" in table.rows[0].columns[1].text


@pytest.mark.django_db
def test_filter_partial_match(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, publisher_harpercollins
):
    """icontains lookup should match partial strings."""
    response = client_user_publisher_view.get("/publisher/?name=harper")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 1
    assert "HarperCollins" in table.rows[0].columns[1].text


@pytest.mark.django_db
def test_filter_form_rendered(client_user_publisher_view: Client, cv_publisher, publisher_penguin):
    """The filter form should be present in the response."""
    response = client_user_publisher_view.get("/publisher/")
    content = response.content.decode("utf-8")
    assert 'id="filter-button"' in content
    from lxml import html

    (toggle,) = html.fromstring(response.content).cssselect("#cv-filter-toggle")
    assert toggle.get("data-cv-tooltip") == "context"
    assert toggle.get("title")


def _filter_icon_states(response) -> dict:
    from lxml import html

    doc = html.fromstring(response.content)
    spans = doc.cssselect("#cv-filter-toggle [data-cv-filter-icon]")
    return {s.get("data-cv-filter-icon"): s.get("hidden") is not None for s in spans}


def _filter_toggle_attrs(response) -> dict:
    from lxml import html

    (toggle,) = html.fromstring(response.content).cssselect("#cv-filter-toggle")
    return {"aria-expanded": toggle.get("aria-expanded"), "aria-controls": toggle.get("aria-controls")}


@pytest.mark.django_db
def test_filter_toggle_aria_expanded_follows_state(client_user_publisher_view: Client, cv_publisher, publisher_penguin):
    assert _filter_toggle_attrs(client_user_publisher_view.get("/publisher/")) == {
        "aria-expanded": "false",
        "aria-controls": "filter-collapse",
    }
    client_user_publisher_view.post("/publisher/", data='{"filter_expanded": true}', content_type="application/json")
    assert _filter_toggle_attrs(client_user_publisher_view.get("/publisher/"))["aria-expanded"] == "true"


@pytest.mark.django_db
def test_filter_toggle_icon_collapsed(client_user_publisher_view: Client, cv_publisher, publisher_penguin):
    """Collapsed panel: open icon visible, close icon hidden."""
    response = client_user_publisher_view.get("/publisher/")
    assert _filter_icon_states(response) == {"open": False, "close": True}


@pytest.mark.django_db
def test_filter_toggle_icon_expanded(client_user_publisher_view: Client, cv_publisher, publisher_penguin):
    """Expanded panel (stored in session): close icon visible, open icon hidden."""
    post = client_user_publisher_view.post(
        "/publisher/", data='{"filter_expanded": true}', content_type="application/json"
    )
    assert post.status_code == 200
    response = client_user_publisher_view.get("/publisher/")
    assert _filter_icon_states(response) == {"open": True, "close": False}


@pytest.mark.django_db
def test_toggle_and_panel_follow_cv_filter_expanded(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, monkeypatch
):
    """Both the toggle icon and the panel state read the one view property, not the session directly."""
    view_cls = cv_publisher.get_all_views()["list"]
    monkeypatch.setattr(view_cls, "cv_filter_expanded", property(lambda self: True))
    response = client_user_publisher_view.get("/publisher/")
    assert response.context["cv_filter_expanded"] is True
    assert _filter_icon_states(response) == {"open": True, "close": False}


@pytest.mark.django_db
def test_pinned_filter_is_expanded_without_toggle(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, monkeypatch
):
    from lxml import html

    view_cls = cv_publisher.get_all_views()["list"]
    monkeypatch.setattr(view_cls, "cv_filter_pinned", True)
    response = client_user_publisher_view.get("/publisher/")
    assert response.context["cv_filter_expanded"] is True
    assert html.fromstring(response.content).cssselect("#cv-filter-toggle") == []


# --- the filter actions through the form-button leaf (Phase 6, 06-05) ---------------------------------------------

FILTER_PATH = "/publisher/?sort=name&order=name&dir=desc"
APPLY = ("submit", "submit", "Apply Filter", "filter-button", "btn btn-primary")
RESET = ("reset", "reset", "Reset Filter", "filter-button-reset", "btn btn-secondary")


def _filter_form(response):
    from lxml import html

    assert response.status_code == 200
    (form,) = html.fromstring(response.content).cssselect("form#filter-form")
    return form


def _buttons(form) -> list[tuple]:
    return [(b.get("type"), b.get("name"), b.get("value"), b.get("id"), b.get("class")) for b in form.iter("button")]


def _hidden(form) -> list[tuple]:
    return [(i.get("name"), i.get("value")) for i in form.cssselect("input[type=hidden]")]


def _publisher_list_view():
    from tests.test1.app.views import PublisherListView

    return PublisherListView


@pytest.mark.django_db
def test_filter_endpoint_renders_apply_and_reset_as_leaf_buttons(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin
):
    """Apply / Reset are layout <button>s with their original type, name, value, id and classes."""
    form = _filter_form(client_user_publisher_view.get(FILTER_PATH))
    assert _buttons(form) == [APPLY, RESET]
    assert [" ".join(b.text_content().split()) for b in form.iter("button")] == ["Apply Filter", "Reset Filter"]
    # no visible action is left behind as a crispy input
    assert form.cssselect("input[type=submit], input[type=reset]") == []


@pytest.mark.django_db
def test_filter_endpoint_fields_then_actions_then_hidden_wrapper(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin
):
    """Field layout, one action group, then the pack-owned hidden-input wrapper with its margin/classes."""
    form = _filter_form(client_user_publisher_view.get(FILTER_PATH))
    order = [el.get("name") for el in form.iter("input", "button")]
    assert order == ["name", "submit", "reset", "sort", "order", "dir"]

    apply_, reset = form.iter("button")
    group = apply_.getparent().getparent()
    assert reset.getparent().getparent() is group
    assert group.get("class").split() == ["mb-3"]
    assert apply_.getparent().get("class") == ""

    hidden = form.cssselect("input[type=hidden]")
    wrapper = hidden[0].getparent().getparent()
    assert all(el.getparent().getparent() is wrapper for el in hidden)
    assert (wrapper.get("class"), hidden[0].getparent().get("class")) == ("mb-3", "")
    # the hidden wrapper is a separate, later sibling and holds no visible action
    assert wrapper is not group and wrapper.getparent() is group.getparent()
    siblings = list(group.getparent())
    assert siblings.index(group) < siblings.index(wrapper)
    assert wrapper.cssselect("button, input[type=submit], input[type=reset]") == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (FILTER_PATH, [("sort", "name"), ("order", "name"), ("dir", "desc")]),
        ("/publisher/", [("sort", "")]),
        ("/publisher/?sort=&order=&dir=", [("sort", "")]),
        ("/publisher/?order=name", [("sort", ""), ("order", "name")]),
    ],
)
def test_filter_hidden_controls_unchanged(client_user_publisher_view: Client, cv_publisher, path, expected):
    form = _filter_form(client_user_publisher_view.get(path))
    assert _hidden(form) == expected
    assert _buttons(form) == [APPLY, RESET]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("modes", "apply_mode", "reset_mode"),
    [({}, "label", "label"), ({"filter-submit": "icon", "filter-reset": "both"}, "icon", "both")],
)
def test_filter_actions_honor_the_list_view_form_modes(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, monkeypatch, modes, apply_mode, reset_mode
):
    """The filter helper's view owns its actions: label / both / icon with the filter and filter-reset icons."""
    monkeypatch.setattr(_publisher_list_view(), "cv_form_actions_label_mode", modes)
    form = _filter_form(client_user_publisher_view.get(FILTER_PATH))
    apply_, reset = form.iter("button")
    for button, mode, icon_class, label in (
        (apply_, apply_mode, "fa-filter", "Apply Filter"),
        (reset, reset_mode, "fa-rotate-left", "Reset Filter"),
    ):
        (span,) = button.cssselect("span")
        assert span.text == label
        inline = button.cssselect("i")
        if mode == "label":
            assert inline == [] and not span.get("class") and button.get("title") is None
        elif mode == "both":
            assert icon_class in inline[0].get("class") and not span.get("class") and button.get("title") is None
        else:
            assert icon_class in inline[0].get("class") and span.get("class") == "visually-hidden"
            assert (button.get("title"), button.get("data-cv-tooltip")) == (label, "form")
    assert (apply_.get("id"), reset.get("id")) == ("filter-button", "filter-button-reset")


@pytest.mark.django_db
def test_filter_helper_without_layout_renders_form_fields_then_one_action_group(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, monkeypatch
):
    from crud_views.lib.views.list import ListViewFilterFormHelper

    class NoLayoutHelper(ListViewFilterFormHelper):
        pass

    monkeypatch.setattr(_publisher_list_view(), "formhelper_class", NoLayoutHelper)
    for _ in range(2):
        form = _filter_form(client_user_publisher_view.get(FILTER_PATH))
        assert [el.get("name") for el in form.iter("input", "button")] == [
            "name",
            "submit",
            "reset",
            "sort",
            "order",
            "dir",
        ]
        assert _buttons(form) == [APPLY, RESET]
    assert NoLayoutHelper.layout is None


@pytest.mark.django_db
def test_custom_helper_constructor_without_form_keyword(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, monkeypatch
):
    """The mixin keeps constructing helpers with view/request only, so a two-argument constructor still works."""
    from tests.test1.app.views import PublisherFilterFormHelper

    calls = []

    class TwoArgHelper(PublisherFilterFormHelper):
        def __init__(self, view, request):
            calls.append((type(view).__name__, request.method))
            super().__init__(view, request)

    monkeypatch.setattr(_publisher_list_view(), "formhelper_class", TwoArgHelper)
    form = _filter_form(client_user_publisher_view.get(FILTER_PATH))
    assert calls == [("PublisherListView", "GET")]
    assert _buttons(form) == [APPLY, RESET]
    assert _hidden(form) == [("sort", "name"), ("order", "name"), ("dir", "desc")]


@pytest.mark.django_db
def test_filter_endpoint_repeated_requests_never_accumulate_actions(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin
):
    """D-03: the shared class layout of the documented subclass is never extended by a request."""
    from tests.test1.app.views import PublisherFilterFormHelper

    class_layout = PublisherFilterFormHelper.layout
    before = len(class_layout.fields)
    for path in (FILTER_PATH, "/publisher/?order=name", FILTER_PATH):
        form = _filter_form(client_user_publisher_view.get(path))
        assert _buttons(form) == [APPLY, RESET]
    assert PublisherFilterFormHelper.layout is class_layout
    assert len(class_layout.fields) == before


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("?sort=s&o=name&d=asc&order=x&dir=y", [("sort", "s"), ("o", "name"), ("d", "asc")]),
        ("?o=&d=", [("sort", "")]),
        ("?d=desc", [("sort", ""), ("d", "desc")]),
    ],
)
def test_filter_hidden_controls_follow_renamed_order_params(query, expected):
    """Renamed order / direction parameters and empty values keep today's hidden-input naming and value logic."""
    from types import SimpleNamespace

    from crispy_forms.layout import Hidden
    from django.test import RequestFactory

    from crud_views.lib.views.list import ListViewFilterFormHelper

    view = SimpleNamespace(cv_order_param="o", cv_order_dir_param="d")
    helper = ListViewFilterFormHelper(view=view, request=RequestFactory().get("/" + query))
    assert [type(i) for i in helper.inputs] == [Hidden] * len(expected)
    assert [(i.name, i.value) for i in helper.inputs] == expected
    assert helper.view is view
