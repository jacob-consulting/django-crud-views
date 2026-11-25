"""Migration guidance for narrowed hooks and shared consumers before the 1.0 freeze."""

import pytest

from tests.test1.test_label_mode_docs import CHANGELOG_MD, DOCS, MIGRATING_MD, _anchors, _flat, _section


def test_link_access_breaking_entry_names_both_hooks_and_links_the_migration_anchor():
    breaking = _section(_section(CHANGELOG_MD.read_text(), "## Unreleased"), "### Breaking")
    heading = "- **Link access hooks**"
    assert breaking.count(heading) == 1
    entry = breaking[breaking.index(heading) :]
    if "\n- **" in entry[1:]:
        entry = entry[: entry.index("\n- **", 1)]
    for name in (
        "cv_has_access",
        "cv_action_enabled",
        "cv_create_has_access",
        "ParentContextButton",
        "cv_context_has_permission",
        "#412 stage 3a",
        "Bulk toolbar eligibility",
        "Nested-object Cancel",
        "guard state",
        "Navbar child items",
    ):
        assert name in entry
    assert "docs/migrating-1.0.md#link-access-hooks" in entry
    assert "link-access-hooks" in _anchors(MIGRATING_MD)


def test_link_access_migration_section_names_the_override_cases():
    section = _flat(_section(MIGRATING_MD.read_text(), "## Link access hooks"))
    for phrase in (
        "parent from obj",
        "page object from obj",
        "cv_create_has_access(user, rendering_view, parent_obj)",
        "rendering_view is None",
        "ancestor guard",
        "without a resolved parent",
        "GuardianQuerysetMixin",
        "GuardianParentPermissionMixin",
        "cv_has_access override receives None",
        "cv_get_parent_object()",
        "no longer decides the list page's create control",
    ):
        assert phrase in section


def test_link_access_migration_section_lists_the_create_hook_sites():
    section = _flat(_section(MIGRATING_MD.read_text(), "## Link access hooks"))
    for phrase in (
        "ChildContextButton",
        "CardAction",
        "navbar",
        "ParentContextButton",
        "cv_context_has_permission",
        "child object page",
        "child list page",
        "SiblingContextButton",
        "create page itself",
        "stay hidden",
        "cv_has_access on a nested Guardian create no longer affects package links",
        "key_target",
        "page's own create decides",
    ):
        assert phrase in section


def test_nested_guardian_create_migration_section_is_rewritten():
    section = _flat(_section(MIGRATING_MD.read_text(), "### Nested Guardian create access"))
    assert "cv_has_access" in section
    assert "denies every argument" in section
    assert "cv_create_has_access" in section
    assert "replacement" in section
    assert "works as before" not in section
    assert "Keep passing the page object" not in section
    assert {"child-link-parent-permissions", "nested-guardian-create-access"} <= _anchors(MIGRATING_MD)


def test_link_check_is_not_in_the_stability_inventory():
    assert "link_access" not in (DOCS / "development" / "stability.md").read_text()
    section = _flat(_section(MIGRATING_MD.read_text(), "## Link access hooks"))
    assert "no public checker API" in section
    assert "remain later work" in section


@pytest.mark.parametrize(
    "change",
    (
        "Permission denial skips state",
        "Nested targets check known ancestors",
        "Missing guard state denies nested links",
        "Bulk toolbar eligibility uses the check directly",
        "Bulk returns follow Cancel eligibility",
        "Create hooks receive the matching rendering view",
        "Nested-object Cancel asks for the parent",
        "Core create state and parent-button objects use guard state",
    ),
)
def test_link_access_migration_names_each_approved_consumer_change(change):
    section = _flat(_section(MIGRATING_MD.read_text(), "### Eight consumer changes in stage 3a"))
    assert change in section


def test_link_access_migration_has_exact_view_identity_parent_hook_and_return_guidance():
    section = _flat(_section(MIGRATING_MD.read_text(), "## Link access hooks"))
    for phrase in (
        "rendering_view.cv_viewset is target.cv_viewset",
        "origin, fallback, success URL",
        "authorization responses and login redirects do not change",
        "parent ViewSet's get_queryset()",
        "rather than a parent view's queryset",
        "Exceptions from a custom parent hook propagate, including its Http404",
        "unknown level stays None, unchecked",
        "parent view without change",
    ):
        assert phrase in section


def test_link_access_direct_call_actor_guidance_does_not_imply_request_fallback():
    section = _flat(_section(MIGRATING_MD.read_text(), "### Direct calls must supply the actor"))
    for phrase in (
        "view.cv_get_context(key, obj=obj, user=request.user)",
        "omitted user or explicit user=None",
        "may raise even when view.request.user exists",
        "does not infer it",
        "separate from the valid own-object None",
        "ContextButton uses its request-bound path",
    ):
        assert phrase in section


def test_link_access_migration_bounds_each_retained_guardian_mechanism():
    section = _flat(_section(MIGRATING_MD.read_text(), "## Link access hooks"))
    for phrase in (
        "page seam",
        "list-page rewrite",
        "navbar child item uses neither seam nor rewrite",
        "even on the create target's own ViewSet page (D-55)",
        "queryset-only Guardian composition still skips its nearest gate",
        "Cancel to its nested list check known higher ancestors",
        "L2) survives only where no higher level is gated",
        "GuardianParentPermissionMixin retains its separate immediate-only path",
    ):
        assert phrase in section


def test_link_access_owned_sections_do_not_retain_stage_one_consumer_limits():
    sections = (
        _section(MIGRATING_MD.read_text(), "## Link access hooks"),
        _section(MIGRATING_MD.read_text(), "## Child-link parent permissions"),
        (DOCS / "reference/context_buttons.md").read_text(),
    )
    for section in sections:
        for obsolete in (
            "evaluate state independently",
            "evaluated independently of permission",
            "Sibling links and ordinary row actions still have no parent gate",
            "Core controls do not disappear",
            "Rendering checks only the supplied immediate parent",
        ):
            assert obsolete not in section


def test_reference_pages_state_the_narrowed_meaning():
    passages = (
        (
            "reference/guardian.md",
            "### What the create access helpers accept",
            ("cv_create_has_access", "cv_has_access", "denies every argument"),
        ),
        (
            "reference/context_buttons.md",
            "### `cv_context_has_permission` — gate surrounding markup",
            ("Two cases stay False on purpose",),
        ),
        ("reference/action_enabled.md", "## The `obj` Parameter", ("nested list",)),
        (
            "reference/navbar.md",
            "## Labels, access and empty output",
            ("link check", "parent gate, own access, state hook"),
        ),
        ("reference/card-list-view.md", "## Child ViewSet Actions", ("cv_create_has_access",)),
        (
            "faq.md",
            "### Gate surrounding markup by permission",
            ("cv_create_has_access", "parent the request resolved from the URL", "Two", "False", "kept on purpose"),
        ),
    )
    for path, heading, statements in passages:
        section = _flat(_section((DOCS / path).read_text(), heading))
        for statement in statements:
            assert statement in section, (path, statement)
