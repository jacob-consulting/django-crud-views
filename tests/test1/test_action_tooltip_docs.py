"""Execute the exact published action tooltip migrations with authorized view data."""

import re
from pathlib import Path

import pytest
from django.template import Context, Template
from django.utils.functional import lazy
from lxml import html

from crud_views.lib.view import CardAction, ContextButton
from crud_views.lib.view.button_data import cv_button_data
from crud_views.lib.view.visibility import cv_resolve_action
from tests.test1.app.views import AuthorDetailView, AuthorUpdateView, cv_author
from tests.test1.test_action_label_mode_render import AUTHOR_FULL, AUTHOR_VIEW, _client, _detail_view
from tests.test1.test_label_mode_docs import _row, _section

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference/buttons.md"


def recipe(name):
    """Preserve exact UTF-8 fence body bytes for the browser fixture's SHA-256 identity."""
    text = REFERENCE.read_bytes().decode("utf-8")
    marker = f"<!-- tooltip-recipe: {name} -->"
    assert text.splitlines().count(marker) == 1, f"Expected exactly one {marker}"
    matches = re.findall(rf"^{re.escape(marker)}\n```django\n(.*?)\n```(?=\n|$)", text, re.M | re.S)
    assert len(matches) == 1, f"Expected one complete django fence for {name}"
    return matches[0]


def rendered(name, data):
    return html.fragment_fromstring(Template(recipe(name)).render(Context(data)), create_parent=True)


def test_recipe_contract():
    for name in ("action-leaf", "menu-leaf", "raw-context"):
        body = recipe(name)
        Template(body)
        if name != "raw-context":
            assert f'data-tooltip-recipe="{name}"' in body
            assert not re.search(r"tags/button/(?:action|menu_item)\.html", body)
            assert not re.search(r"{%\s*cv_(?:button|render_button)\s", body)
        else:
            assert '{% cv_button "context" %}' in body


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["action-leaf", "menu-leaf"])
@pytest.mark.parametrize("location", ["context", "list", "card"])
@pytest.mark.parametrize("mode", ["icon", "label", "both"])
@pytest.mark.parametrize("key", ["update", "detail", "ping"])
def test_copied_leaves_use_real_action_data(author_douglas_adams, monkeypatch, name, location, mode, key):
    client = _client([AUTHOR_FULL])
    if location == "card":
        response = client.get("/author/card/")
        assert response.status_code == 200
        view = response.context["view"]
        raw = view.cv_get_card_action_data(
            CardAction(key=key, label="Card caption", label_mode=mode), author_douglas_adams, view.request.user
        )
    else:
        view, request = _detail_view(client, author_douglas_adams)
        monkeypatch.setattr(type(view), f"cv_{location}_actions_label_mode", {key: mode})
        raw = view.cv_get_context(key, obj=author_douglas_adams, user=request.user, location=location)
    resolved = cv_resolve_action(raw)
    assert resolved is not None
    data = cv_button_data(resolved, location, "action" if name == "action-leaf" else "menu-item")
    (node,) = rendered(name, data).xpath("./*[@cv-key]")
    assert node.get("data-tooltip-recipe") == name
    assert node.get("cv-key") == key
    assert node.tag == ("button" if key == "ping" else "a")
    if key == "ping":
        assert node.get("data-cv-action") == "submit-form"
        assert node.get("data-cv-target") == f"cv_form_{raw['cv_oid']}"
    else:
        assert node.get("href") == raw["cv_url"]
    if key == "detail" and location != "card":
        assert node.get("aria-current") == "page"
        assert "active" in node.get("class").split()
    short = "Card caption" if location == "card" else str(raw["cv_action_short_label"] or raw["cv_action_label"])
    full = "Card caption" if location == "card" else str(raw["cv_action_label"])
    icon = name == "action-leaf" and mode == "icon"
    assert node.get("title") == (short if icon else None)
    assert node.get("data-cv-tooltip") == (location if icon else None)
    assert node.text_content().strip() == (full if icon else short)
    assert bool(node.cssselect("span.visually-hidden")) is icon


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["action-leaf", "menu-leaf"])
@pytest.mark.parametrize("state", ["modal", "disabled-modal", "disabled-post"])
def test_copied_state_branches(author_douglas_adams, monkeypatch, name, state):
    key = "ping" if state == "disabled-post" else "update"
    target = cv_author.get_view_class(key)
    monkeypatch.setattr(target, "cv_modal", state != "disabled-post")
    monkeypatch.setattr(target, "cv_modal_size", "lg")
    disabled = state.startswith("disabled")
    if disabled:
        monkeypatch.setattr(target, "cv_has_access", classmethod(lambda cls, user, obj=None: False))
        monkeypatch.setattr(target, "cv_inaccessible_actions", "disable")
    view, request = _detail_view(_client([AUTHOR_FULL]), author_douglas_adams)
    raw = view.cv_get_context(key, obj=author_douglas_adams, user=request.user, location="context")
    data = cv_button_data(cv_resolve_action(raw), "context", "action" if name == "action-leaf" else "menu-item")
    (node,) = rendered(name, data).xpath("./*[@cv-key]")
    assert node.get("data-tooltip-recipe") == name
    assert node.tag == ("button" if disabled else "a")
    assert (node.get("disabled") is not None) is disabled
    if disabled:
        assert node.get("data-cv-disabled") == "permission"
        for attr in ("href", "data-cv-modal", "data-cv-modal-size", "data-cv-action", "data-cv-target", "aria-current"):
            assert node.get(attr) is None
    else:
        assert node.get("href") == raw["cv_url"]
        assert node.get("data-cv-modal") == "true"
        assert node.get("data-cv-modal-size") == "lg"


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["action-leaf", "menu-leaf"])
@pytest.mark.parametrize("short", [None, "", "Short", "Full"])
@pytest.mark.parametrize("full", ["", "Full"])
def test_caption_fallback_and_empty_titles(author_douglas_adams, name, short, full):
    view, request = _detail_view(_client([AUTHOR_FULL]), author_douglas_adams)
    raw = view.cv_get_context("update", obj=author_douglas_adams, user=request.user, location="context")
    raw.update(cv_action_label=full, cv_action_short_label=short)
    data = cv_button_data(cv_resolve_action(raw), "context", "action" if name == "action-leaf" else "menu-item")
    (node,) = rendered(name, data).xpath("./*[@cv-key]")
    expected_title = (short or full or None) if name == "action-leaf" else None
    assert node.get("title") == expected_title
    assert node.get("data-cv-tooltip") == ("context" if expected_title else None)
    assert node.text_content().strip() == (full if name == "action-leaf" else short or full)


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["action-leaf", "menu-leaf"])
@pytest.mark.parametrize("caption_source", ["plain", "lazy", "interpolated"])
def test_recipe_escaping(author_douglas_adams, monkeypatch, name, caption_source):
    payload = '" onmouseover="alert(1)"><script>雪 & café</script>'
    author_douglas_adams.first_name = payload
    author_douglas_adams.save()
    if caption_source == "interpolated":
        monkeypatch.setattr(AuthorUpdateView, "cv_action_label_template_code", "Full {{ object.first_name }}")
        monkeypatch.setattr(AuthorUpdateView, "cv_action_short_label_template_code", "Short {{ object.first_name }}")
    view, request = _detail_view(_client([AUTHOR_FULL]), author_douglas_adams)
    raw = view.cv_get_context("update", obj=author_douglas_adams, user=request.user, location="context")
    if caption_source != "interpolated":
        factory = (lambda value: lazy(lambda: value, str)()) if caption_source == "lazy" else str
        raw.update(cv_action_label=factory(f"Full {payload}"), cv_action_short_label=factory(f"Short {payload}"))
    data = cv_button_data(cv_resolve_action(raw), "context", "action" if name == "action-leaf" else "menu-item")
    (node,) = rendered(name, data).xpath("./*[@cv-key]")
    assert node.get("onmouseover") is None
    assert not node.cssselect("script")
    assert node.text_content().strip() == f"{'Full' if name == 'action-leaf' else 'Short'} {payload}"
    assert node.get("title") == (f"Short {payload}" if name == "action-leaf" else None)


@pytest.mark.django_db
@pytest.mark.parametrize("policy", ["allowed", "hide", "disable"])
@pytest.mark.parametrize("key", ["update", "ping"])
def test_raw_context_recipe_normalizes_permissions_and_custom_label(author_douglas_adams, monkeypatch, policy, key):
    target = cv_author.get_view_class(key)
    monkeypatch.setattr(target, "cv_modal", key == "update")
    monkeypatch.setattr(target, "cv_inaccessible_actions", "disable" if policy == "disable" else "hide")
    monkeypatch.setattr(target, "cv_has_access", classmethod(lambda cls, user, obj=None: policy == "allowed"))
    monkeypatch.setattr(target, "cv_action_label_template_code", "{{ object.first_name }}")
    custom = ContextButton(
        key="custom",
        key_target=key,
        template_code=recipe("raw-context"),
        label_template_code="Custom {{ cv_action_label }}",
    )
    monkeypatch.setattr(AuthorDetailView, "cv_context_buttons", [custom])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["custom"])
    author_douglas_adams.first_name = '<script>雪 & "</script>'
    author_douglas_adams.save()
    view, request = _detail_view(_client([AUTHOR_VIEW]), author_douglas_adams)
    raw = view.cv_get_context("custom", obj=author_douglas_adams, user=request.user, location="context")
    assert "cv_tag" not in raw
    assert "cv_title" not in raw
    nodes = rendered("raw-context", raw).xpath(".//*[@cv-key]")
    if policy == "hide":
        assert not nodes
        return
    (node,) = nodes
    assert node.getparent().get("data-app-action") == "custom"
    assert node.text_content().strip() == f"Custom {author_douglas_adams.first_name}"
    assert node.get("title") == f"Custom {author_douglas_adams.first_name}"
    assert not node.cssselect("script")
    if policy == "disable":
        assert node.tag == "button"
        assert node.get("disabled") is not None
        for attr in ("href", "data-cv-modal", "data-cv-action", "data-cv-target"):
            assert node.get(attr) is None
    elif key == "update":
        assert node.get("data-cv-modal") == "true"
    else:
        assert node.get("data-cv-action") == "submit-form"


def test_leaf_rows_and_rendering_diagram_agree():
    section = _section(REFERENCE.read_text(), "### The leaf contract")
    assert "full hidden caption" in _row(section, "`cv_label`")[1]
    assert "icon titles and menu text" in _row(section, "`cv_short_label`")[1]
    title = _row(section, "`cv_title`")[1]
    assert "resolved short caption" in title
    assert "nonempty" in title
    assert "full fallback" in title
    diagram = (ROOT / "docs/reference/context_buttons.md").read_text()
    ricon = re.search(r'RICON\(\["(.*?)"\]\)', diagram)[1]
    assert "full hidden caption" in ricon
    assert "short tooltip" in ricon
    menus = _section((ROOT / "docs/reference/action_menus.md").read_text(), "## Labels, icons and the active action")
    assert "no automatic title or tooltip" in menus


@pytest.mark.django_db
def test_copied_action_missing_icon_uses_effective_visible_mode(author_douglas_adams, settings):
    settings.CRUD_VIEWS_STRICT = False
    view, request = _detail_view(_client([AUTHOR_FULL]), author_douglas_adams)
    raw = view.cv_get_context("update", obj=author_douglas_adams, user=request.user, location="context")
    raw["cv_icon_action"] = None
    (node,) = rendered("action-leaf", cv_button_data(cv_resolve_action(raw), "context")).xpath("./*[@cv-key]")
    assert node.get("title") is None
    assert node.get("data-cv-tooltip") is None
    assert node.text_content().strip() == "Update"
    assert not node.cssselect("span.visually-hidden")


def test_paired_migration_and_both_scan_paths():
    migration = (ROOT / "docs/migrating-1.0.md").read_text()
    changelog = (ROOT / "CHANGELOG.md").read_text().split("### Breaking", 1)[1].split("### ", 1)[0]
    assert "docs/migrating-1.0.md#action-tooltips" in changelog
    for heading in ("### CSS and tests that select on markup", "## Silent breaks"):
        checklist = _section(migration, heading)
        assert "(#action-tooltips)" in checklist
        assert "short" in checklist.lower()
        assert "context-menu native titles" in checklist
    section = _section(migration, "## Action tooltips")
    for anchor in ("copied-action-leaf", "copied-menu-leaf", "raw-contextbutton-template"):
        assert f"(reference/buttons.md#{anchor})" in section
    for phrase in (
        "must migrate immediately",
        "needs no markup edit",
        "changed field semantics",
        "full hidden `cv_label` stays unchanged",
        "remove its native-title branch",
        "explicit card label, short caption, full caption, then key",
        "extra-attribute ownership",
        "Full-caption/helper APIs remain available",
        "visible-label defect was not",
        "hover/focus",
    ):
        assert phrase in " ".join(section.split())
    # Canonical recipes live only in buttons.md, so there is no second copy to drift.
    assert "```" not in section


def test_javascript_caption_and_lifecycle_boundaries():
    tooltips = _section((ROOT / "docs/reference/javascript.md").read_text(), "## Tooltips")
    for phrase in (
        "short caption with full-caption fallback",
        "full hidden caption stays unchanged",
        "neither an automatic `title` nor a marker",
        "cv:modal:loaded",
        "cv:formset:row-added",
        "hide(el)",
        "dispose(el)",
        "next hover or focus",
        "cv.adapters.tooltip = {init() {}}",
        "Application-owned tooltips",
        "filter toggles, property detail, formset controls or card-order controls",
    ):
        assert phrase in " ".join(tooltips.split())
