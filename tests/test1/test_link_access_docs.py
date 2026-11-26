"""Migration guidance for narrowed hooks and shared consumers before the 1.0 freeze."""

import re

import pytest

from crud_views.lib.link_access import LinkAccess
from crud_views.lib.viewset import AncestorPolicy
from tests.test1 import test_link_access as private_link_tests
from tests.test1.app.models import Publisher
from tests.test1.test_ancestor_authorization import _user
from tests.test1.test_ancestor_docs import _fence
from tests.test1.test_ancestor_helpers import _grant
from tests.test1.test_label_mode_docs import CHANGELOG_MD, DOCS, MIGRATING_MD, _anchors, _flat, _section

core_targets = private_link_tests.core_targets
data = private_link_tests.data
helpers = private_link_tests.helpers
LINK_ACCESS_MD = DOCS / "reference/link_access.md"


def _run_public_example(heading, namespace):
    """Execute the complete published fence with only its documented caller inputs."""
    source = _fence(LINK_ACCESS_MD, heading)
    assert "from crud_views.lib.link_access import LinkAccess, check_link_access" in source
    exec(compile(source, f"{LINK_ACCESS_MD}:{heading}", "exec"), namespace)
    return namespace


def test_public_reference_contract():
    page = LINK_ACCESS_MD.read_text()
    flat = _flat(page)
    for phrase in (
        "check_link_access(target, user, *, obj=None, known_ancestors=()) -> LinkAccess",
        "target and user can be positional or keyword arguments",
        "obj and known_ancestors are keyword-only",
        "regular enum",
        "LinkAccess.ALLOWED",
        "LinkAccess.DENIED_PERMISSION",
        "LinkAccess.DENIED_STATE",
        "Both denial members are false",
        "not interchangeable with raw strings",
        "not a supported serialization contract",
        "stable at 1.0",
        "target must be a view class",
        "view instances and other non-class inputs",
        "finite ordered list or tuple",
        "None, iterators and QuerySets",
        "before inspection or evaluation",
        "complete validation before authorization",
        "messages start with check_link_access",
        "target without a ViewSet",
        "ancestor does not fit its declared level",
        "own object does not fit",
        "no own object for an object target",
        "own object for a collection target",
        "more ancestor slots than declared levels",
        "any ancestor slot for a top-level target",
        "trailing None",
        "nearest first",
        "isinstance",
        "concrete model",
        "proxy",
        "multi-table",
        "polymorphic",
        "Resource class",
        "unsaved",
        "does not guarantee permission or request success",
        "parent gates → own permission → state",
        "missing immediate parent",
        "unknown higher slots",
        "cv_action_enabled(user, obj)",
        "immediate parent",
        "Top-level collection",
        "None",
        "no object or ancestor loading",
        "authorization queries and project hook work",
        "broken declared ancestry",
        "its own message",
        "missing ancestor permission key",
        "operation requirements",
        "project hook exceptions propagate",
        "missing own permission key denies",
        "signed-in, active user",
        "provider none",
        "anonymous top-level Guardian list",
        "does not authorize a request",
        "ViewSet querysets",
        "dispatch",
        "has_permission",
        "middleware",
        "membership",
        "another parent",
        "404",
        "cv_get_parent_object",
        "no public accessor for resolved higher ancestors",
        "stricter higher-level permission",
        "cv_create_has_access",
        "rendering-view-dependent override",
        "permission-only function stays private",
        "cv_context_has_permission",
    ):
        assert phrase in flat, phrase
    database = _flat(_section(page, "### Database checks at reached gates"))
    for phrase in (
        "nested ViewSets support only the 'default' database",
        "Nested ancestor gate with a non-none provider | Actor and authorization tables | Supplied ancestor object",
        "Nested permission-enforcing core own gate | Actor and authorization tables | No own-object database check",
        "Nested permission-enforcing Guardian own gate | Actor and authorization tables | Supplied own object",
        "Core own permission does not inspect its own object's database",
        "Top-level targets do not run these nested database checks",
        "a denied actor or earlier gate can stop evaluation before a later check",
        "Unknown or unselected ancestor gates do not perform these checks",
    ):
        assert phrase in database, phrase
    assert "guardian.md#parent-only-non-create-limitation" in page
    assert "parent-only-non-create-limitation" in _anchors(DOCS / "reference/guardian.md")
    assert "context_buttons.md#cv_context_has_permission-gate-surrounding-markup" in page
    assert "cv_context_has_permission-gate-surrounding-markup" in _anchors(DOCS / "reference/context_buttons.md")
    index = _section((DOCS / "reference/index.md").read_text(), "## Actions & navigation")
    assert "[Link access](link_access.md)" in index
    nav = (DOCS / "reference/.pages").read_text().split("- Actions & navigation:", 1)[1].split("- Extensions:", 1)[0]
    assert "- link_access.md" in nav


@pytest.mark.django_db
@pytest.mark.parametrize("example", ["object", "nested", "off-page"])
def test_public_documented_examples(core_targets, helpers, data, monkeypatch, example):
    if example == "object":
        actor = _user("docs_object", (Publisher, "view"))
        namespace = {"TargetView": core_targets.Detail, "user": actor, "book": data.book, "publisher": data.penguin}
        heading = "## Object target"
    elif example == "nested":
        actor = _user("docs_nested", (Publisher, "view"))
        namespace = {"BookList": core_targets.List, "user": actor, "publisher": data.penguin}
        heading = "## Nested collection"
    else:
        actor = _user("docs_off_page")
        _grant(actor, helpers.pub, "view", data.penguin)
        _grant(actor, helpers.book, "view", data.book)
        monkeypatch.setattr(helpers.note.vs, "ancestor_policy", AncestorPolicy(cascade=True))
        namespace = {"NoteList": helpers.note.List, "user": actor, "book": data.book, "publisher": data.penguin}
        heading = "## Off-page caller"
    result = _run_public_example(heading, namespace)
    assert result["result"] is LinkAccess.ALLOWED
    assert result["show_link"] is True


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
        "#413 stage 3b",
        "Bulk toolbar eligibility",
        "Nested-object Cancel",
        "guard state",
        "Navbar child items",
        "ContextButton.get_context",
        'key_target="create"',
        "signed-in and active",
        "Parent-only non-create",
        "repeats its bounded immediate-parent check",
    ):
        assert name in entry
    assert "docs/migrating-1.0.md#link-access-hooks" in entry
    assert "link-access-hooks" in _anchors(MIGRATING_MD)


def test_public_checker_added_entry():
    unreleased = _section(CHANGELOG_MD.read_text(), "## Unreleased")
    added = _section(unreleased, "### Added")
    heading = "- **Public link access**"
    assert added.count(heading) == 1
    entry = added[added.index(heading) :].split("\n\n", 1)[0]
    for phrase in ("check_link_access", "LinkAccess", "stable", "supplied", "permission", "state"):
        assert phrase in entry, phrase
    assert "docs/reference/link_access.md" in entry
    assert "[#414](https://github.com/jacob-consulting/django-crud-views/issues/414)" in entry
    assert unreleased.count("#414") == 1
    breaking = _section(unreleased, "### Breaking")
    assert heading not in breaking
    assert "check_link_access" not in breaking
    assert breaking.count("- **Link access hooks**") == 1


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
        "ManyToMany child page with a known route parent",
        "cv_has_access on a nested Guardian create no longer affects package links",
        "key_target",
        "actual target's result",
        "ContextButton.get_context implementation",
        "output is no longer corrected by key",
        "Move custom create permission logic to cv_create_has_access",
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


def test_link_check_is_in_the_stability_inventory():
    text = (DOCS / "development/stability.md").read_text()
    assert "**Link access**" in text
    inventory = _flat(text.split("**Link access**", 1)[1].split("\n\n**", 1)[0])
    for phrase in (
        "crud_views.lib.link_access",
        "check_link_access",
        "LinkAccess",
        "LinkAccess.ALLOWED",
        "LinkAccess.DENIED_PERMISSION",
        "LinkAccess.DENIED_STATE",
        "stable at 1.0",
        "regular enum",
        "Both denial members are false",
        "../reference/link_access.md",
        "keyword-only",
    ):
        assert phrase in inventory, phrase
    assert "all names prefixed with an underscore" in text
    assert "`_link_access`" not in text
    assert "`_link_permission`" not in text


@pytest.mark.parametrize(
    "path, heading, marker, link",
    [
        (
            "migrating-1.0.md",
            "## Link access hooks",
            "6. Review a custom",
            "reference/link_access.md",
        ),
        (
            "reference/guardian.md",
            "### Create button visibility for child viewsets",
            "Each button follows its actual target.",
            "link_access.md",
        ),
        (
            "reference/context_buttons.md",
            "## ContextButton",
            "Custom `ContextButton.get_context` output",
            "link_access.md",
        ),
        (
            "migrating-1.0.md",
            "### Nested Guardian create access",
            "Custom `ContextButton.get_context` output",
            "reference/link_access.md",
        ),
    ],
)
def test_public_checker_migration_pointers(path, heading, marker, link):
    section = _section((DOCS / path).read_text(), heading)
    paragraph = section[section.index(marker) :].split("\n\n", 1)[0]
    flat = _flat(paragraph)
    for phrase in ("check_link_access", "complete", "cv_create_has_access", "custom create permission"):
        assert phrase in flat, (path, heading, phrase)
    assert f"]({link})" in paragraph, (path, heading, link)
    assert ((DOCS / path).parent / link).resolve() == LINK_ACCESS_MD.resolve()
    assert "bounded" in flat or "direct-hook bounds" in flat, (path, heading, flat)


def test_documentation_public_checker_claims():
    obsolete = re.compile(
        r"\bno public (?:link )?checker\b"
        r"|\bpublic (?:link )?checker\b[^.]*\b(?:not available|not published|later work|future work|pending)\b"
        r"|\bno\b[^.]*\bpublic checker\b[^.]*\bintroduced\b"
        r"|\bpublication(?: and validation)? of a standalone function remains? later work\b",
        re.IGNORECASE,
    )
    offending = []
    for path in sorted(DOCS.rglob("*.md")):
        prose = _flat(re.sub(r"```.*?```", "", path.read_text(), flags=re.DOTALL))
        offending.extend((str(path.relative_to(DOCS)), match.group()) for match in obsolete.finditer(prose))
    assert not offending, offending
    for path in (MIGRATING_MD, DOCS / "reference/guardian.md", DOCS / "reference/nested.md"):
        assert "no public accessor for resolved ancestors" in _flat(path.read_text()), path
    guardian = _flat(_section((DOCS / "reference/guardian.md").read_text(), "#### Limits and configuration failures"))
    for phrase in ("independent table columns", "LinkChildColumn", "DataPanel/DataView", "breadcrumbs", "site menus"):
        assert phrase in guardian, phrase
    assert "opt-in" in guardian
    filter_section = _section(
        (DOCS / "reference/context_buttons.md").read_text(),
        "### `cv_context_has_permission` — gate surrounding markup",
    )
    assert "[check_link_access](link_access.md)" in filter_section
    assert "they remain permission-only and never ask state" in _flat(filter_section)


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


def test_link_access_migration_bounds_create_overrides_and_parent_only_cancel():
    section = _flat(_section(MIGRATING_MD.read_text(), "## Link access hooks"))
    for phrase in (
        "Every nested Guardian link requires a signed-in, active actor",
        "Actor admission and declared parent gates run before cv_create_has_access",
        "A denied gate skips the override",
        "a false override still denies after the gates pass",
        "default hook deliberately repeats its bounded immediate-parent check",
        "It does not discover or check higher ancestors and never evaluates state",
        "ambiguous M2M own child denies",
        "explicit route-known M2M parent is accepted",
        "now checks its declared immediate-parent policy as well as known higher ancestors",
        "Navbar child items already used aligned ancestors on every page (D-55)",
        "page create controls now apply those same known higher gates",
        "Guardian object/list/create Cancel also checks known higher ancestors",
        "link can be hidden when the request allows",
        "A plain base follows its ordinary own hook",
        "Cancel does not ask cv_has_access for this shape, whether inherited or overridden",
        "No explicit-versus-inherited override distinction is supported",
    ):
        assert phrase in section


def test_primary_guardian_guidance_removes_ended_denials_with_bounded_direct_hook_advice():
    migration = MIGRATING_MD.read_text()
    guardian = (DOCS / "reference/guardian.md").read_text()
    passages = (
        _section(migration, "## Link access hooks"),
        _section(migration, "### Nested Guardian create access"),
        _section(guardian, "### Create button visibility for child viewsets"),
        _section(guardian, "### What the create access helpers accept"),
        _section(guardian, "### Parent-to-child collection links"),
        _section((DOCS / "faq.md").read_text(), "### Gate surrounding markup by permission"),
    )
    for passage in passages:
        flat = _flat(passage)
        for obsolete in (
            "create page itself stay hidden",
            "filter stays False",
            "still skips the immediate-parent gate",
            "retains its separate immediate-only path",
            "retained-create-and-cancel-mechanisms",
            "possible future enhancement",
        ):
            assert obsolete not in flat
    create = _flat(_section(guardian, "### Create button visibility for child viewsets"))
    for phrase in (
        "signed-in, active actor",
        "Actor admission and declared parent gates run before cv_create_has_access at every consumer",
        "A denied gate skips even a true override without super()",
        "false override still denies",
        "default cv_create_has_access deliberately repeats the bounded immediate-parent check",
        "do not discover or check higher ancestors and never evaluate state",
        "ContextButton.get_context output",
        "Move custom create permission logic to cv_create_has_access",
        "rendering_view.cv_viewset is target.cv_viewset",
    ):
        assert phrase in create
    limitation = _flat(_section(guardian, "### Parent-only non-create limitation"))
    for phrase in (
        "PermissionRequired base",
        "child model permission that the request does not require",
        "A plain base follows its ordinary own hook",
        "Cancel omits cv_has_access entirely",
        "including both inherited and custom overrides",
        "known higher ancestors, the immediate parent and state",
        "No explicit-versus-inherited override distinction is supported",
    ):
        assert phrase in limitation


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
            (
                "Child-list and M2M filters can return True",
                "they remain permission-only and never ask state",
                "known higher gates precede this hook",
                "ambiguous M2M own child denies",
            ),
        ),
        (
            "reference/action_enabled.md",
            "## The `obj` Parameter",
            (
                "nested list",
                "Cancel (core and Guardian) alone retains",
                "Higher ancestors still come only from guard state",
            ),
        ),
        (
            "reference/navbar.md",
            "## Labels, access and empty output",
            ("link check", "parent gate, own access, state hook"),
        ),
        (
            "reference/card-list-view.md",
            "## Child ViewSet Actions",
            (
                "cv_create_has_access",
                "Own card create actions use the resolved URL parent",
                "child card actions use the row their URL is built from",
                "Both check all known declared higher gates before the create hook",
            ),
        ),
        (
            "faq.md",
            "### Gate surrounding markup by permission",
            (
                "cv_create_has_access",
                "parent the request resolved from the URL",
                "Child-list and M2M filters can now return True",
                "independently of state",
                "ambiguous M2M child still denies",
            ),
        ),
    )
    for path, heading, statements in passages:
        section = _flat(_section((DOCS / path).read_text(), heading))
        for statement in statements:
            assert statement in section, (path, statement)
