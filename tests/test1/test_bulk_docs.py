"""Keep the published bulk recipes and their security boundaries in step with the code."""

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "docs/reference/bulk_actions.md"
SECTIONS = (
    "Classes",
    "Basic usage",
    "Selection on tables and cards",
    "How a submission is handled",
    "Confirmation",
    "Eligible and blocked records",
    "Scope and permissions",
    "Selection limit",
    "Result message and return",
    "Bulk delete",
    "Row locking",
    "Review templates",
    "Toolbar buttons",
    "JavaScript",
    "System checks",
    "Limits",
)
STABLE_NAMES = (
    "crud_views.lib.bulk",
    "BulkSelectionMixin",
    "BulkFormViewPermissionRequired",
    "BulkConfirmForm",
    "cv_bulk_actions",
    "cv_bulk_max",
    "cv_bulk_confirm",
    "cv_bulk_objects",
    "cv_bulk_has_permission",
    "cv_bulk_check",
    "cv_bulk_header",
    "cv_bulk_ids",
    "cv_bulk_blocked_ids",
    "cv_bulk_stage",
    "bulk_review",
    "objects",
    "blocked",
    "pk",
    "label",
    "reasons",
    "crud_views/view_bulk_form.html",
    "crud_views/view_bulk_form.content.html",
    "crud_views/snippets/bulk_toolbar.html",
    "crud_views/columns/bulk_select.html",
    "crud_views/snippets/message/bulk.html",
    "crud_views/snippets/bulk/blocked.html",
    "crud_views/snippets/bulk/eligible.html",
    "data-cv-bulk",
    "data-cv-bulk-item",
    "data-cv-bulk-all",
    "data-cv-bulk-count",
    "data-cv-bulk-action",
    "data-cv-bulk-enhanced",
    "bulk:toolbar",
    "bulk:controls",
    "bulk:select-all",
    "bulk:checkbox",
    "bulk:actions",
    "bulk:card-cell",
    "bulk:card-select",
    "`bulk`",
)
INTERNAL_NAMES = ("cv_bulk_form_id", "cv_bulk_buttons", "blocked_items.html", "snippets/paragraph/bulk.html")


def guide():
    assert GUIDE.is_file(), "The bulk reference guide must exist"
    return GUIDE.read_text()


def section(text, heading):
    return text.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]


def normalized(text):
    return " ".join(text.split())


def python_blocks(text):
    return re.findall(r"```python\n(.*?)\n```", text, re.S)


def test_bulk_guide_structure_and_live_link():
    text = guide()
    assert text.startswith('# Bulk actions\n\n!!! example "Try it live"')
    assert "https://django-crud-views-demo.onrender.com/bulk-selection/document/" in text
    assert re.findall(r"^## (.+)$", text, re.M) == list(SECTIONS)
    assert len(text.splitlines()) >= 250
    for name in STABLE_NAMES:
        assert name in text, name
    for name in INTERNAL_NAMES:
        assert name not in text, name


def test_bulk_basic_recipe_and_mixin_placement():
    basic = section(guide(), "Basic usage")
    assert "DocumentListView(BulkSelectionMixin, ListViewTableMixin, ListViewPermissionRequired)" in basic
    assert "ArchiveDocumentsView(BulkFormViewPermissionRequired)" in basic
    for name in (
        "cv_key",
        "cv_path",
        "cv_permission",
        "cv_action_label_template_code",
        "cv_action_short_label_template_code",
        "cv_bulk_check",
        "cv_form_valid",
        "self.cv_bulk_objects",
    ):
        assert name in basic
    selection = normalized(section(guide(), "Selection on tables and cards"))
    assert "before `ListViewTableMixin`" in selection
    assert "before the card view base" in selection
    assert "must be the first" not in selection
    for name in (
        "get_table_kwargs",
        "super()",
        "BreadcrumbMixin",
        "cv_bulk_select",
        "cv_card_template",
        "str(record)",
        "__str__",
        "one bulk source per page",
    ):
        assert name in selection


def test_bulk_submission_and_confirmation_contract():
    submission = normalized(section(guide(), "How a submission is handled"))
    for name in (
        "cv_bulk_ids",
        "cv_bulk_blocked_ids",
        "cv_bulk_stage",
        "cv_bulk_",
        "review",
        "execute",
        "multipart",
        "read-only",
        "viewset.E279",
        "cv_form_valid_hook",
        "cv_get_atomic()",
    ):
        assert name in submission
    assert "does not call `cv_form_valid_process`" in submission
    assert "override of `cv_form_valid_process` has no effect" in submission
    assert "write belongs in `cv_form_valid`" in submission
    confirmation = section(guide(), "Confirmation")
    rows = [line for line in confirmation.splitlines() if line.startswith("|")]
    assert len(rows) == 7  # Header, separator, and the five D-04 outcomes.
    for name in ("cv_bulk_confirm", "declares fields", "cv_modal = True", "viewset.E251", "stock", "full page"):
        assert name in normalized(confirmation)


def test_bulk_scope_and_eligibility_are_not_source_filters():
    scope = normalized(section(guide(), "Scope and permissions"))
    for name in (
        "submitted IDs",
        "ViewSet queryset",
        "destination queryset",
        "parent scope",
        "True",
        "crud_views_guardian.W002",
        "has_perm",
        "SILENCED_SYSTEM_CHECKS",
        "form choices",
    ):
        assert name in scope
    assert "source list is no authorization gate" in scope
    assert "shared restrictions belong in the ViewSet" in scope
    eligible = normalized(section(guide(), "Eligible and blocked records"))
    for name in (
        "cv_bulk_has_permission",
        "cv_bulk_check",
        "read-only",
        "informational",
        "remains excluded",
        "no stored",
        "once per request",
        "without a label",
        "writes nothing",
    ):
        assert name in eligible


def test_bulk_limits_describe_actual_database_guards():
    limits = normalized(section(guide(), "Limits"))
    for name in (
        "Django ORM",
        "default database",
        "single scalar primary key",
        "ViewSet queryset",
        "get_queryset()",
        "cv_get_db_alias()",
        "own database",
        "write route",
        "ImproperlyConfigured",
        "not skipped",
        "values()",
        "values_list()",
        "does not intercept",
        "composite keys",
        "Resources",
    ):
        assert name in limits
    assert "`cv_form_valid` must write through `cv_get_db_alias()`" in limits
    selection = section(guide(), "Selection limit")
    for name in ("cv_bulk_max", "100", "990", "DATA_UPLOAD_MAX_NUMBER_FIELDS", "excluded", "before loading"):
        assert name in selection


def test_bulk_return_and_message_limits():
    result = normalized(section(guide(), "Result message and return"))
    assert "origin, else `cv_cancel_key`, else the success URL" in result
    for name in (
        "warning redirect",
        "plain GET",
        "all-blocked",
        "same three steps",
        "stock Cancel button",
        "not rendered",
        "cv_success_key",
        "cv_success_keys",
        "viewset.W275",
        "first page",
        "filter",
        "sort",
        "page",
        "JavaScript",
        "singular",
        "plural",
        "cv_message_template_code",
        "1 record processed.",
        "N records processed.",
        "inside the transaction",
        "may still be shown",
        "request_lifecycle.md#hook-reference",
    ):
        assert name in result
    assert "accessible success URL" not in result
    assert "success URL is accessible" not in result


def test_bulk_delete_shares_rule_and_keeps_inspection_step_separate():
    delete = section(guide(), "Bulk delete")
    blocks = python_blocks(delete)
    leaf = next(block for block in blocks if "cv_check_delete_protection" in block)
    assert leaf.count("return document_delete_errors(") == 2
    assert "inspect_deletion" not in leaf
    for name in (
        "inspect_deletion",
        "related.protected",
        "complete",
        "locked subfolder",
        "parent",
        "not caught",
        "cv_atomic",
        "on-commit failure is not a rollback",
        "queued",
    ):
        assert name in normalized(delete)


def test_bulk_locking_recipe_rejects_missing_and_changed_records_before_write():
    locking = section(guide(), "Row locking")
    assert "The library takes no row locks." in locking
    (block,) = python_blocks(locking)
    tree = ast.parse(block)
    method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "cv_form_valid")
    assert "select_for_update()" in ast.unparse(method)
    comparisons = [node for node in ast.walk(method) if isinstance(node, ast.Compare)]
    assert any(ast.unparse(node) == "len(rows) != len(keys)" for node in comparisons)
    guards = [node for node in method.body if isinstance(node, ast.If)]
    assert len(guards) == 2
    assert all(any(isinstance(node, ast.Raise) for node in guard.body) for guard in guards)
    assert "cv_bulk_check" in ast.unparse(guards[1].test)
    assert method.body.index(guards[-1]) < next(i for i, node in enumerate(method.body) if isinstance(node, ast.For))
    for name in (
        "deleted after the check",
        "whole submission",
        "cv_bulk_has_permission",
        "default manager",
        "ViewSet and destination querysets",
        "differently per database",
        "distinct()",
        "aggregation",
    ):
        assert name in normalized(locking)


def test_bulk_review_and_toolbar_public_contract():
    review = section(guide(), "Review templates")
    for name in ("bulk_review", "objects", "blocked", "pk", "label", "reasons", "hidden", "every record"):
        assert name in review
    toolbar = normalized(section(guide(), "Toolbar buttons"))
    for name in (
        "submit buttons",
        "form:submit",
        "visible text",
        "hidden text",
        "tooltip",
        "short action label",
        "cv_icon_action",
        "full action label",
        "header of the review page",
        "bulk",
        "both",
        "CRUD_VIEWS_LABEL_MODE_DEFAULTS",
        "no per-action map",
        "no variant",
        "buttons.md#bulk-selection-classes",
    ):
        assert name in toolbar
    assert "javascript.md#bulk-selection-toolbar" in section(guide(), "JavaScript")


def test_bulk_check_table_matches_implementation():
    checks = section(guide(), "System checks")
    rows = "\n".join(line for line in checks.splitlines() if line.startswith("|"))
    actual = set(re.findall(r"(?:viewset|crud_views_guardian)\.[EW]\d+", rows))
    source = (ROOT / "src/crud_views/lib/bulk/__init__.py").read_text()
    expected = {f"viewset.{value}" for value in re.findall(r'id="([EW]\d+)"', source)}
    guardian = (ROOT / "src/crud_views_guardian/checks.py").read_text()
    assert "crud_views_guardian.W002" in guardian
    assert actual == expected | {"crud_views_guardian.W002"}
    for name in ("paginate_by", "table_pagination", "get_paginate_by()", "without pagination"):
        assert name in checks


def test_bulk_python_recipes_parse():
    blocks = python_blocks(guide())
    assert blocks
    for block in blocks:
        ast.parse(block)


def test_bulk_stability_inventory():
    text = (ROOT / "docs/development/stability.md").read_text()
    assert "**Bulk actions**" in text
    bulk = text.split("**Bulk actions**", 1)[1].split("\n\n**", 1)[0]
    for name in STABLE_NAMES:
        assert name in bulk, name
    for name in INTERNAL_NAMES:
        assert name not in text
    assert "stable at 1.0" in bulk
    assert "no bulk-specific provisional exception" in bulk
    assert "../reference/bulk_actions.md" in bulk


def test_bulk_hook_exception_beside_stability_hook_inventory():
    text = (ROOT / "docs/development/stability.md").read_text()
    paragraph = normalized(next(part for part in text.split("\n\n") if "**Declared attributes and hooks**" in part))
    for name in (
        "does not call `cv_form_valid_process`",
        "BulkFormViewPermissionRequired",
        "cv_form_valid",
        "cv_form_valid_hook",
        "cv_get_atomic()",
        "has no effect",
        "../reference/bulk_actions.md#how-a-submission-is-handled",
    ):
        assert name in paragraph


def test_bulk_lifecycle_note_preserves_existing_post_advice():
    text = (ROOT / "docs/reference/request_lifecycle.md").read_text()
    paragraph = normalized(next(part for part in text.split("\n\n") if "own the transaction" in part))
    for name in (
        "call them instead of",
        "does not call `cv_form_valid_process`",
        "BulkFormViewPermissionRequired",
        "has no effect",
        "bulk_actions.md#how-a-submission-is-handled",
        "eligibility inside the transaction",
    ):
        assert name in paragraph
    assert paragraph.index("bound invalid responses.") < paragraph.index("BulkFormViewPermissionRequired")


def test_bulk_guardian_warning_location_and_item_policy():
    text = (ROOT / "docs/reference/guardian.md").read_text()
    assert "## Bulk actions" in text
    bulk = normalized(section(text, "Bulk actions"))
    for name in (
        "cv_bulk_has_permission",
        "True",
        "crud_views_guardian.W002",
        "has_perm",
        "obj",
        "SILENCED_SYSTEM_CHECKS",
        "get_queryset()",
        "bulk_actions.md",
        "Django",
        "system checks",
        "manage.py check",
        "runserver",
        "migrate",
    ):
        assert name in bulk
    assert "manage page of a Guardian ViewSet does not list" in bulk


def test_bulk_message_reference_and_added_changelog():
    messages = (ROOT / "docs/reference/messages.md").read_text()
    assert "crud_views/snippets/message/bulk.html" in messages
    assert "bulk_actions.md#result-message-and-return" in messages
    text = section((ROOT / "CHANGELOG.md").read_text(), "Unreleased")
    added = text.split("### Added\n", 1)[1].split("\n### ", 1)[0]
    for name in ("(#387)", "BulkSelectionMixin", "BulkFormViewPermissionRequired", "docs/reference/bulk_actions.md"):
        assert name in added
    assert "#387" not in text.split("### Breaking\n", 1)[1].split("\n### ", 1)[0]


@pytest.mark.parametrize(
    "page",
    [
        "list_view.md",
        "card-list-view.md",
        "custom_form_view.md",
        "guardian.md",
        "buttons.md",
        "javascript.md",
        "messages.md",
    ],
)
def test_bulk_seven_reference_links(page):
    text = (ROOT / "docs/reference" / page).read_text()
    assert re.search(r"\]\(bulk_actions\.md(?:#[\w-]+)?\)", text), page


def test_bulk_index_link_follows_action_view():
    text = (ROOT / "docs/reference/index.md").read_text()
    assert text.count("bulk_actions.md") == 1
    lines = section(text, "Actions & navigation").splitlines()
    action = next(i for i, line in enumerate(lines) if "[ActionView]" in line)
    assert lines[action + 1].startswith("- [Bulk actions](bulk_actions.md)")
    assert "current-page" in lines[action + 1]


def test_bulk_source_reference_composition_guidance():
    table = normalized(section((ROOT / "docs/reference/list_view.md").read_text(), "Bulk selection"))
    assert "`BulkSelectionMixin` before `ListViewTableMixin`" in table
    assert "cv_bulk_actions" in table
    card = normalized(section((ROOT / "docs/reference/card-list-view.md").read_text(), "Bulk selection"))
    for name in (
        "BulkSelectionMixin",
        "before the card view base",
        "cv_bulk_actions",
        "bulk:card-cell",
        "bulk:card-select",
    ):
        assert name in card
    form = normalized(section((ROOT / "docs/reference/custom_form_view.md").read_text(), "Bulk action forms"))
    for name in ("BulkFormViewPermissionRequired", "permission-required", "non-object", "own base class"):
        assert name in form


def test_bulk_theme_and_script_links_are_in_bulk_sections():
    buttons = (ROOT / "docs/reference/buttons.md").read_text()
    bulk = buttons.split("### Bulk selection classes\n", 1)[1].split("\n### ", 1)[0]
    assert "bulk_actions.md" in bulk
    script = section((ROOT / "docs/reference/javascript.md").read_text(), "Bulk selection toolbar")
    assert "bulk_actions.md" in script
