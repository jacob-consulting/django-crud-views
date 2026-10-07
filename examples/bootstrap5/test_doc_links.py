"""Examples <-> docs cross-link checks.

Each ``Feature.docs`` entry (project/features.py) must point at an existing ``docs/`` page and, if it has an
anchor, at a real heading on that page. Each referenced page must link back to the feature's live-demo landing
page. Checked against the repo's ``docs/``, not the published site: the demo links to Read the Docs ``stable``,
so anchors added on main only resolve online after the next release.
"""

import re
import unicodedata
from pathlib import Path

import pytest
from project.features import FEATURES

EXAMPLES_DIR = Path(__file__).resolve().parent
DOCS_DIR = EXAMPLES_DIR.parents[1] / "docs"

HEADING_RE = re.compile(r"^#{1,6}\s+(?P<text>.+?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})")
LINK_TARGET_RE = re.compile(r"\]\((?P<url>https?://[^)\s]+)\)")


def slugify(value: str, separator: str = "-") -> str:
    """Copy of Python-Markdown's ``markdown.extensions.toc.slugify`` -- the mkdocs default anchor algorithm.

    Copied rather than imported: ``markdown`` is not installed in the ``examples`` nox session.
    """
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(rf"[{separator}\s]+", separator, value)


def unfenced_lines(markdown: str):
    """Lines outside fenced code blocks. A fence closes only on the same character with at least its length."""
    fence = ""
    for line in markdown.splitlines():
        if fence:
            closing = line.strip()
            if set(closing) == {fence[0]} and len(closing) >= len(fence):
                fence = ""
            continue
        if m := FENCE_RE.match(line):
            fence = m["fence"]
            continue
        yield line


def heading_slugs(markdown: str) -> set[str]:
    """Anchor slugs of all ATX headings, skipping lines inside fenced code blocks."""
    return {slugify(m["text"]) for line in unfenced_lines(markdown) if (m := HEADING_RE.match(line))}


def demo_links(markdown: str) -> set[str]:
    """Link targets inside ``!!! example`` admonitions -- the "Try it live" boxes."""
    links, in_box = set(), False
    for line in unfenced_lines(markdown):
        if line.startswith("!!! example"):
            in_box = True
            continue
        if in_box and line.strip() and not line.startswith("    "):
            in_box = False
        if in_box:
            links.update(m["url"] for m in LINK_TARGET_RE.finditer(line))
    return links


@pytest.mark.parametrize(
    "heading, slug",
    [
        ("Down: table links and `ChildContextButton`", "down-table-links-and-childcontextbutton"),
        ("`polymorphic_forms`", "polymorphic_forms"),
        ("Kind 1 — Conditional field-group in a form", "kind-1-conditional-field-group-in-a-form"),
        ("The `cv_property_display` DSL", "the-cv_property_display-dsl"),
        ("Signed choices (single combo, no buttons)", "signed-choices-single-combo-no-buttons"),
    ],
)
def test_slugify_matches_mkdocs(heading, slug):
    assert slugify(heading) == slug


def test_heading_slugs_ignore_fenced_code():
    markdown = "# Title\n\n## Real heading\n\n```python\n# urls.py\n## not a heading\n```\n\n### After fence\n"
    assert heading_slugs(markdown) == {"title", "real-heading", "after-fence"}


def test_heading_slugs_fence_closes_only_on_matching_marker():
    # a fence closes only on the same character with at least the opening length
    markdown = "~~~\n```\n## inside\n```\n~~~\n\n## After\n\n````\n```\n## inside too\n```\n````\n"
    assert heading_slugs(markdown) == {"after"}


def test_demo_links_only_counts_link_targets_in_example_boxes():
    markdown = (
        "Prose mentions https://x/nested/company/ without linking.\n\n"
        "```\n[code](https://x/in-code/)\n```\n\n"
        '!!! example "Try it live"\n'
        "    The [Nested](https://x/nested/company/) and the\n"
        "    [Showcase](https://x/showcase/recipe/1/) examples.\n\n"
        "After the box: [later](https://x/after/)\n"
    )
    assert demo_links(markdown) == {"https://x/nested/company/", "https://x/showcase/recipe/1/"}


def test_every_feature_declares_doc_refs():
    for feature in FEATURES:
        assert feature.docs, f"{feature.app} has no documentation references"


def iter_doc_refs():
    return [
        pytest.param(feature, ref, id=f"{feature.app}:{ref.page}#{ref.anchor}")
        for feature in FEATURES
        for ref in feature.docs
    ]


@pytest.mark.parametrize("feature, ref", iter_doc_refs())
def test_doc_ref_resolves(feature, ref):
    page = DOCS_DIR / ref.page
    assert page.is_file(), f"{feature.app}: docs page {ref.page!r} does not exist under docs/"
    if ref.anchor:
        slugs = heading_slugs(page.read_text(encoding="utf-8"))
        assert ref.anchor in slugs, f"{feature.app}: no heading with anchor #{ref.anchor} in {ref.page}"


DEMO_BASE = "https://django-crud-views-demo.onrender.com"


def iter_backlinks():
    """One case per (feature, distinct referenced page); a page referenced twice by one app is checked once."""
    return [
        pytest.param(feature, page, id=f"{feature.app}:{page}")
        for feature in FEATURES
        for page in dict.fromkeys(ref.page for ref in feature.docs)
    ]


@pytest.mark.parametrize("feature, page", iter_backlinks())
def test_docs_page_links_back_to_demo(feature, page):
    from django.urls import reverse

    demo_url = DEMO_BASE + reverse(feature.url_name)
    links = demo_links((DOCS_DIR / page).read_text(encoding="utf-8"))
    assert demo_url in links, (
        f"docs/{page} has no 'Try it live' box linking to the {feature.title} example ({demo_url})"
    )
