"""Phase 06 FORM-01 / D-17: before-change goldens of the package form buttons, captured from real endpoints.

Byte convention: a golden holds the exact raw response substrings of the captured controls, in document order, each
followed by one ``"\\n"``, encoded as UTF-8 and compared with ``read_bytes()``. Controls are extracted from the
response rather than the page being normalized, so the random CSRF token and unrelated page content never enter a
golden; whitespace inside a control is kept as rendered. There is no DOM re-serialization and no update-on-test
mode: the fixtures were written once from unchanged product source and are only ever compared here.

The extractor accepts ``<input>`` and ``<button>`` controls alike, so the button migration (06-02) reuses it
unchanged and every golden diff is product markup. Defaults are pinned a second time by parsed DOM assertions.
"""

import re
import uuid
from pathlib import Path

import pytest
from django.test import Client
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

# golden name -> (logged-in client fixture, page path, captured control names, expected default controls)
CRUD_CASES = {
    "create": ("client_user_author_add", "/author/create/", ("submit", "reset"), (SUBMIT, CANCEL)),
    "update": ("client_user_author_change", f"/author/{AUTHOR_PK}/update/", ("submit", "reset"), (SUBMIT, CANCEL)),
    "delete": ("client_user_author_delete", f"/author/{AUTHOR_PK}/delete/", ("delete", "reset"), (DELETE, CANCEL)),
}


def _crud_controls(request, case: str) -> list[str]:
    client_fixture, path, names, _ = CRUD_CASES[case]
    client: Client = request.getfixturevalue(client_fixture)
    with translation.override("en"):
        response = client.get(path)
    assert response.status_code == 200
    return _extract_controls(response.content.decode("utf-8"), names)


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(CRUD_CASES))
def test_form_button_baselines(request, golden_author, case):
    """The raw control bytes of the real create / update / delete pages equal their committed golden."""
    data = _golden_bytes(_crud_controls(request, case))
    assert b"csrfmiddlewaretoken" not in data
    assert data == (GOLDEN_DIR / f"{case}.html").read_bytes()


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(CRUD_CASES))
def test_form_button_baselines_are_deterministic(request, golden_author, case):
    assert _golden_bytes(_crud_controls(request, case)) == _golden_bytes(_crud_controls(request, case))


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(CRUD_CASES))
def test_form_button_defaults(request, golden_author, case):
    """Default text, name, value, id, type and classes, independently of the golden bytes."""
    expected = CRUD_CASES[case][3]
    elements = [_element(control) for control in _crud_controls(request, case)]
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
