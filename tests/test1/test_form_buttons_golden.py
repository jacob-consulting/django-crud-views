"""Phase 06 FORM-01 / D-17: before-change goldens of the package form buttons, captured from real endpoints.

Byte convention: a golden holds the exact raw response substrings of the captured controls, in document order, each
followed by one ``"\\n"``, encoded as UTF-8 and compared with ``read_bytes()``. Controls are extracted from the
response rather than the page being normalized, so the random CSRF token and unrelated page content never enter a
golden; whitespace inside a control is kept as rendered. There is no DOM re-serialization and no update-on-test
mode: the fixtures were written once from unchanged product source and are only ever compared here.

The extractor accepts ``<input>`` and ``<button>`` controls alike, so the button migration (06-02) reuses it
unchanged and every golden diff is product markup. Defaults are pinned a second time by parsed DOM assertions.

Updates (D-17): 06-02 task 3 replaced the create / update / delete / workflow goldens with the form-button leaf
output after comparing the parsed controls with the before-change baselines (commits 2956f3e and 98b71ed, which stay
in history): native type, name, value, id, classes, cancel URL and visible text are equal; only the element and its
body changed (``<input>`` to ``<button>`` with a ``<span>`` label). 06-05 replaced the filter golden the same way,
reusing ``_extract_filter_form_region`` unchanged (its definition equals the one in baseline commit 98b71ed): Apply /
Reset moved from the pack's trailing inputs wrapper into one layout ``FormActions`` group of leaf buttons after the
fields; the hidden sort / order / dir inputs keep that wrapper, its classes and their names / values.

The filter golden is different on purpose (L-FILTER-GOLDEN-SCOPE): ``_extract_filter_form_region`` returns the exact
raw response slice from the unique ``<form id="filter-form" ...>`` opening tag through its matching ``</form>`` —
fields, visible actions and the pack-owned hidden-input wrapper — by source offsets, never DOM serialization or
whitespace normalization. 06-05 reuses this extractor unchanged, so its filter diff is product markup only.
"""

import re
import uuid
from pathlib import Path
from typing import NamedTuple

import pytest
from django.test import Client, override_settings
from django.utils import translation
from lxml import html as lxml_html

GOLDEN_DIR = Path(__file__).parent / "golden" / "form_buttons"

# fixed primary key: an object URL in a control (e.g. a cancel target) must not vary between runs
AUTHOR_PK = uuid.UUID("6f1c2b1e-5d4a-4c3b-9a8e-0f1e2d3c4b5a")

# one start tag of a form control; quoted attribute values may contain ">"
_START_TAG = re.compile(r"""<(input|button)\b(?:[^>"']|"[^"]*"|'[^']*')*>""")
_NAME = re.compile(r'(?<![\w-])name="([^"]*)"')


def _extract_controls(markup: str, names: tuple[str, ...]) -> list[str]:
    """The raw markup of the controls submitting one of ``names``, in document order; each name exactly once.

    An ``<input>`` is its start tag; a ``<button>`` runs through its closing tag (buttons do not nest).
    """
    found: list[tuple[str, str]] = []
    for match in _START_TAG.finditer(markup):
        name = _NAME.search(match.group(0))
        if name is None or name.group(1) not in names:
            continue
        if match.group(1) == "input":
            control = match.group(0)
        else:
            end = markup.find("</button>", match.end())
            assert end != -1, f"unclosed button control {name.group(1)!r}"
            control = markup[match.start() : end + len("</button>")]
        found.append((name.group(1), control))
    counts = {name: [n for n, _ in found].count(name) for name in names}
    assert all(count == 1 for count in counts.values()), counts
    return [control for _, control in found]


def _golden_bytes(controls: list[str]) -> bytes:
    return "".join(f"{control}\n" for control in controls).encode("utf-8")


def _element(control: str):
    return lxml_html.fragment_fromstring(control)


def _type(element) -> str:
    return element.get("type") or ("submit" if element.tag == "button" else "text")


def _text(element) -> str:
    """The text a user sees: an input's value, a button's collapsed text content."""
    if element.tag == "input":
        return element.get("value")
    return " ".join(element.text_content().split())


@pytest.fixture
def golden_author():
    from tests.test1.app.models import Author

    return Author.objects.create(pk=AUTHOR_PK, first_name="Douglas", last_name="Adams")


# the test app's AuthorForm sets submit_label = "Create" for both its create and update pages
SUBMIT = {"type": "submit", "name": "submit", "value": "Create", "id": "submit-id-submit", "class": "btn btn-primary"}
DELETE = {"type": "submit", "name": "delete", "value": "Delete", "id": "submit-id-delete", "class": "btn btn-primary"}
CANCEL = {
    "type": "button",
    "name": "reset",
    "value": "Cancel",
    "id": "button-id-reset",
    "class": "btn btn-secondary",
    "data-cv-cancel-url": "/author/",
}

WORKFLOW_SUBMIT = {**SUBMIT, "value": "Process Workflow Step"}
WORKFLOW_CANCEL = {**CANCEL, "data-cv-cancel-url": "/campaign/"}


class ControlCase(NamedTuple):
    client: str  # logged-in client fixture
    obj: str | None  # fixture of the object the page is about; its pk fills {pk}
    path: str
    names: tuple[str, ...]  # captured control names, each exactly once
    expected: tuple[dict, ...]  # default controls, in document order


# golden name -> case; each golden is tests/test1/golden/form_buttons/<name>.html
CONTROL_CASES = {
    "create": ControlCase("client_user_author_add", None, "/author/create/", ("submit", "reset"), (SUBMIT, CANCEL)),
    "update": ControlCase(
        "client_user_author_change", "golden_author", "/author/{pk}/update/", ("submit", "reset"), (SUBMIT, CANCEL)
    ),
    "delete": ControlCase(
        "client_user_author_delete", "golden_author", "/author/{pk}/delete/", ("delete", "reset"), (DELETE, CANCEL)
    ),
    "workflow": ControlCase(
        "client_user_campaign_change",
        "campaign_new",
        "/campaign/{pk}/workflow/",
        ("submit", "reset"),
        (WORKFLOW_SUBMIT, WORKFLOW_CANCEL),
    ),
}


def _page_controls(request, case: str) -> list[str]:
    spec = CONTROL_CASES[case]
    client: Client = request.getfixturevalue(spec.client)
    pk = request.getfixturevalue(spec.obj).pk if spec.obj else None
    with translation.override("en"):
        response = client.get(spec.path.format(pk=pk))
    assert response.status_code == 200
    return _extract_controls(response.content.decode("utf-8"), spec.names)


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(CONTROL_CASES))
def test_form_button_baselines(request, case):
    """The raw control bytes of the real create / update / delete / workflow pages equal their committed golden."""
    data = _golden_bytes(_page_controls(request, case))
    assert b"csrfmiddlewaretoken" not in data
    assert data == (GOLDEN_DIR / f"{case}.html").read_bytes()


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(CONTROL_CASES))
def test_form_button_baselines_are_deterministic(request, case):
    assert _golden_bytes(_page_controls(request, case)) == _golden_bytes(_page_controls(request, case))


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(CONTROL_CASES))
def test_form_button_defaults(request, case):
    """Default text, name, value, id, type and classes, independently of the golden bytes."""
    expected = CONTROL_CASES[case].expected
    elements = [_element(control) for control in _page_controls(request, case)]
    assert len(elements) == len(expected)
    for element, attrs in zip(elements, expected, strict=True):
        assert _type(element) == attrs["type"]
        assert element.get("name") == attrs["name"]
        assert element.get("value") == attrs["value"]
        assert element.get("id") == attrs["id"]
        assert element.get("class") == attrs["class"]
        assert element.get("data-cv-cancel-url") == attrs.get("data-cv-cancel-url")
        assert _text(element) == attrs["value"]


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(CONTROL_CASES))
def test_layout_controls_are_form_leaf_buttons(request, case):
    """The intended structural change (06-02): each layout control is one <button> whose body is its label span."""
    expected = CONTROL_CASES[case].expected
    for control, attrs in zip(_page_controls(request, case), expected, strict=True):
        element = _element(control)
        assert element.tag == "button"
        assert [child.tag for child in element] == ["span"]
        assert element[0].text == attrs["value"] and not element[0].get("class")
        assert element.get("title") is None and element.get("data-cv-tooltip") is None


@pytest.mark.django_db
def test_delete_control_submits_delete_name_and_value(client_user_author_delete, golden_author):
    """The rendered delete control is the clicked submitter of the delete POST: name="delete", value="Delete"."""
    with translation.override("en"):
        markup = client_user_author_delete.get(f"/author/{AUTHOR_PK}/delete/").content.decode("utf-8")
    (control,) = _extract_controls(markup, ("delete",))
    element = _element(control)
    assert (element.get("name"), element.get("value"), _type(element)) == ("delete", "Delete", "submit")


@pytest.mark.django_db
def test_delete_post_with_clicked_submitter(client_user_author_delete, golden_author):
    """New clicked-submitter regression (M-PAYLOAD): confirmation plus the delete button's own name/value deletes.

    test_crud.py keeps its separate confirmation-only POST; this case sends what a browser sends on click.
    """
    from tests.test1.app.models import Author

    response = client_user_author_delete.post(f"/author/{AUTHOR_PK}/delete/", {"confirm": True, "delete": "Delete"})
    assert response.status_code == 302
    assert response.url == "/author/"
    assert not Author.objects.filter(pk=AUTHOR_PK).exists()


def test_extractor_accepts_input_and_button_controls():
    markup = (
        '<div><button class="navbar-toggler" type="button">x</button>'
        '<input type="submit"\n    name="submit"\n    value="a &gt; b"\n    />\n'
        '<button type="button" name="reset" value="Cancel" data-cv-cancel-url="/x/">\n<span>Cancel</span>\n</button>'
        '<input type="hidden" name="other" value="1"></div>'
    )
    assert _extract_controls(markup, ("submit", "reset")) == [
        '<input type="submit"\n    name="submit"\n    value="a &gt; b"\n    />',
        '<button type="button" name="reset" value="Cancel" data-cv-cancel-url="/x/">\n<span>Cancel</span>\n</button>',
    ]
    with pytest.raises(AssertionError):
        _extract_controls(markup, ("submit", "missing"))


# --- filter form: the whole raw form#filter-form region (L-FILTER-GOLDEN-SCOPE) ---

_FORM_TAG = re.compile(r"""<form\b(?:[^>"']|"[^"]*"|'[^']*')*>|</form\s*>""", re.IGNORECASE)
_FILTER_FORM_ID = re.compile(r'(?<![\w-])id="filter-form"')

# stable nonempty sort / order / direction values: each becomes a hidden control of the filter helper
FILTER_PATH = "/publisher/?sort=name&order=name&dir=desc"
FILTER_HIDDEN = [("sort", "name"), ("order", "name"), ("dir", "desc")]


def _extract_filter_form_region(markup: str) -> str:
    """The exact raw slice from the unique ``<form id="filter-form" ...>`` opening tag through its matching
    ``</form>``, found by source offsets (no DOM serialization, no whitespace normalization)."""
    tags = list(_FORM_TAG.finditer(markup))
    openers = [m for m in tags if not m.group(0).startswith("</") and _FILTER_FORM_ID.search(m.group(0))]
    assert len(openers) == 1, f"expected one form#filter-form, found {len(openers)}"
    (opener,) = openers
    depth = 0
    for match in tags:
        if match.start() < opener.start():
            continue
        depth += -1 if match.group(0).startswith("</") else 1
        if depth == 0:
            return markup[opener.start() : match.end()]
    raise AssertionError("form#filter-form is not closed")


def _filter_region(client: Client) -> str:
    with translation.override("en"):
        response = client.get(FILTER_PATH)
    assert response.status_code == 200
    return _extract_filter_form_region(response.content.decode("utf-8"))


@pytest.mark.django_db
def test_filter_form_baseline(client_user_publisher_view, cv_publisher, publisher_penguin):
    """The raw filter-form region of the real publisher list equals its committed golden."""
    assert _filter_region(client_user_publisher_view).encode("utf-8") == (GOLDEN_DIR / "filter.html").read_bytes()


FILTER_CONTROLS = ("name", "submit", "reset", "sort", "order", "dir")


@pytest.mark.django_db
def test_filter_form_controls_match_golden(client_user_publisher_view, cv_publisher, publisher_penguin):
    """The raw field, Apply / Reset leaf and hidden controls equal the golden's, byte for byte.

    Independent of the template pack's own wrapper markup (field label, FormActions ``<div>``), whose whitespace
    differs between crispy-bootstrap5 releases; the region golden above pins it for the locked pack, while the
    ``crispy_floor`` nox session relies on this test at the declared floors.
    """
    golden = (GOLDEN_DIR / "filter.html").read_text(encoding="utf-8")
    live = _filter_region(client_user_publisher_view)
    expected = _extract_controls(golden, FILTER_CONTROLS)
    assert _golden_bytes(_extract_controls(live, FILTER_CONTROLS)) == _golden_bytes(expected)
    assert [_element(control).tag for control in expected] == ["input", "button", "button", "input", "input", "input"]


@pytest.mark.django_db
def test_filter_form_region_is_stable_and_csrf_free(client_user_publisher_view, cv_publisher, publisher_penguin):
    first = _filter_region(client_user_publisher_view)
    assert first == _filter_region(client_user_publisher_view)
    assert first.startswith("<form") and first.endswith("</form>")
    assert "csrfmiddlewaretoken" not in first
    # the region is only the form: no table or other page content is captured
    assert "<table" not in first and "cv-filter-toggle" not in first


@pytest.mark.django_db
def test_filter_form_defaults(client_user_publisher_view, cv_publisher, publisher_penguin):
    """Wrapper classes, control order, hidden names/values and the reset control, independently of the bytes.

    Since 06-05 the visible actions are leaf buttons in one layout FormActions group; the hidden controls stay in the
    pack's trailing inputs wrapper (L-HIDDEN-WRAPPER), after the actions.
    """
    form = lxml_html.fragment_fromstring(_filter_region(client_user_publisher_view))
    assert (form.get("id"), form.get("method")) == ("filter-form", "get")
    assert form.cssselect("#id_name")[0].get("name") == "name"

    controls = [el for el in form.iter("input", "button") if el.get("name") != "name"]
    assert [(el.get("id") or el.get("name")) for el in controls] == [
        "filter-button",
        "filter-button-reset",
        "sort",
        "order",
        "dir",
    ]

    apply_, reset = controls[:2]
    assert (_type(apply_), apply_.get("name"), apply_.get("value"), apply_.get("class")) == (
        "submit",
        "submit",
        "Apply Filter",
        "btn btn-primary",
    )
    assert _text(apply_) == "Apply Filter"
    assert (_type(reset), reset.get("name"), reset.get("value"), reset.get("class")) == (
        "reset",
        "reset",
        "Reset Filter",
        "btn btn-secondary",
    )
    assert reset.get("id") == "filter-button-reset"
    assert _text(reset) == "Reset Filter"

    hidden = controls[2:]
    assert [(el.get("type"), el.get("name"), el.get("value")) for el in hidden] == [
        ("hidden", name, value) for name, value in FILTER_HIDDEN
    ]
    # the actions are leaf buttons in one FormActions group: div.mb-3 > div[class=""] > button, no duplicates
    assert [el.tag for el in (apply_, reset)] == ["button", "button"]
    assert len(form.cssselect("#filter-button")) == len(form.cssselect("#filter-button-reset")) == 1
    group = apply_.getparent().getparent()
    assert reset.getparent() is apply_.getparent() and apply_.getparent().get("class") == ""
    assert group.get("class").split() == ["mb-3"]
    # the hidden controls keep the pack's trailing inputs wrapper (div.mb-3 > div[class=""]), after the actions
    wrapper = hidden[0].getparent().getparent()
    for el in hidden:
        inner = el.getparent()
        assert el.tag == "input" and inner.tag == "div" and inner.get("class") == ""
        assert inner.getparent() is wrapper and wrapper.get("class") == "mb-3"
    assert wrapper is not group and list(form).index(group) < list(form).index(wrapper)
    assert wrapper.cssselect("button, input[type=submit], input[type=reset]") == []


def test_filter_region_extractor_scope():
    markup = (
        '<form id="other"></form><div><form id="filter-form" method="get">\n'
        '<input type="hidden" name="sort" value="a &gt; b"> </form></div><form id="after"></form>'
    )
    assert _extract_filter_form_region(markup) == (
        '<form id="filter-form" method="get">\n<input type="hidden" name="sort" value="a &gt; b"> </form>'
    )
    with pytest.raises(AssertionError):
        _extract_filter_form_region('<form id="filter-form"></form><form id="filter-form"></form>')


# --- opt-in cancel links (Phase 6.1, D-14, D-17): configured pages, separate from the default byte baselines ---
#
# Every case below runs inside a scoped override_settings; nothing is registered on the theme (review A8). Links are
# parsed on their own: _extract_controls and the committed goldens stay button-only and unchanged.

LINK_SETTINGS = {"CRUD_VIEWS_BUTTON_CLASSES": {"form:cancel-tag": "a"}}
CANCEL_ID = "button-id-reset"


def _page_markup(request, case: str) -> str:
    spec = CONTROL_CASES[case]
    client: Client = request.getfixturevalue(spec.client)
    pk = request.getfixturevalue(spec.obj).pk if spec.obj else None
    with translation.override("en"):
        response = client.get(spec.path.format(pk=pk))
    assert response.status_code == 200
    return response.content.decode("utf-8")


def _owning_form(markup: str, case: str):
    """The form owning the page's unique native action, located by its expected id (review A5)."""
    action_id = CONTROL_CASES[case].expected[0]["id"]
    doc = lxml_html.fromstring(markup)
    (action,) = doc.xpath("//*[@id=$id]", id=action_id)
    assert action.tag == "button"
    form = next(action.iterancestors("form"), None)
    assert form is not None, f"{case}: the native action has no owning form"
    return form, action


def _form_cancel_link(markup: str, case: str):
    """Exactly one a#button-id-reset inside the owning form and no cancel button there; a toolbar link sharing the
    href elsewhere on the page cannot satisfy this."""
    form, action = _owning_form(markup, case)
    links = form.xpath(".//a[@id=$id]", id=CANCEL_ID)
    assert len(links) == 1, f"{case}: {len(links)} cancel links in the owning form"
    assert form.xpath(".//button[@id=$id]", id=CANCEL_ID) == []
    return links[0], action


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(CONTROL_CASES))
def test_configured_page_cancel_is_one_form_scoped_native_link(request, case):
    """D-14/D-15: the configured cancel of each package form is a native link to the page's existing destination."""
    submit, cancel = CONTROL_CASES[case].expected
    with override_settings(**LINK_SETTINGS):
        markup = _page_markup(request, case)
    link, action = _form_cancel_link(markup, case)
    assert link.get("href") == cancel["data-cv-cancel-url"]
    assert (link.get("id"), link.get("class")) == (cancel["id"], cancel["class"])
    assert " ".join(link.text_content().split()) == cancel["value"]
    for omitted in ("name", "value", "type", "data-cv-cancel-url", "disabled", "formnovalidate"):
        assert link.get(omitted) is None, omitted
    # the other action keeps its native submitter identity
    assert (_type(action), action.get("name"), action.get("value")) == ("submit", submit["name"], submit["value"])
    assert (action.get("id"), action.get("class")) == (submit["id"], submit["class"])
    # the raw anchor opening tag carries exactly one href
    (start,) = re.findall(rf"""<a\b(?:[^>"']|"[^"]*"|'[^']*')*\bid="{CANCEL_ID}"(?:[^>"']|"[^"]*"|'[^']*')*>""", markup)
    assert len(re.findall(r"(?<![\w-])href=", start, re.IGNORECASE)) == 1


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(CONTROL_CASES))
def test_configured_page_restores_the_button_after_settings_cleanup(request, case):
    """Before / inside / after on one page: default golden bytes, a configured link, the default bytes again."""
    golden = (GOLDEN_DIR / f"{case}.html").read_bytes()
    assert _golden_bytes(_page_controls(request, case)) == golden
    with override_settings(**LINK_SETTINGS):
        _form_cancel_link(_page_markup(request, case), case)
    assert _golden_bytes(_page_controls(request, case)) == golden
    form, _ = _owning_form(_page_markup(request, case), case)
    assert form.xpath(".//a[@id=$id]", id=CANCEL_ID) == []
    assert len(form.xpath(".//button[@id=$id]", id=CANCEL_ID)) == 1


@pytest.mark.django_db
def test_configured_delete_page_still_deletes_with_its_clicked_submitter(client_user_author_delete, golden_author):
    """The configured delete page renders a cancel link, and its native delete submitter still deletes."""
    from tests.test1.app.models import Author

    with override_settings(**LINK_SETTINGS):
        with translation.override("en"):
            markup = client_user_author_delete.get(f"/author/{AUTHOR_PK}/delete/").content.decode("utf-8")
        link, action = _form_cancel_link(markup, "delete")
        assert link.get("href") == "/author/"
        assert (action.get("name"), action.get("value"), _type(action)) == ("delete", "Delete", "submit")
        response = client_user_author_delete.post(
            f"/author/{AUTHOR_PK}/delete/", {"confirm": True, action.get("name"): action.get("value")}
        )
    assert response.status_code == 302
    assert response.url == "/author/"
    assert not Author.objects.filter(pk=AUTHOR_PK).exists()


@pytest.mark.django_db
def test_configured_filter_form_keeps_native_apply_reset_and_hidden_controls(
    client_user_publisher_view, cv_publisher, publisher_penguin
):
    """Filter Apply / Reset are no cancel: under the link configuration the controls are the golden's, byte for byte."""
    golden = (GOLDEN_DIR / "filter.html").read_text(encoding="utf-8")
    with override_settings(**LINK_SETTINGS):
        live = _filter_region(client_user_publisher_view)
    assert _golden_bytes(_extract_controls(live, FILTER_CONTROLS)) == _golden_bytes(
        _extract_controls(golden, FILTER_CONTROLS)
    )
    form = lxml_html.fragment_fromstring(live)
    assert form.cssselect("a") == []
    assert [el.get("id") for el in form.cssselect("button")] == ["filter-button", "filter-button-reset"]
