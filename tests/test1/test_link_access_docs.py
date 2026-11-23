"""Migration guidance for the narrowed link access hooks before the 1.0 freeze."""

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
