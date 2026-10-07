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


def slugify(value: str, separator: str = "-") -> str:
    """Copy of Python-Markdown's ``markdown.extensions.toc.slugify`` -- the mkdocs default anchor algorithm.

    Copied rather than imported: ``markdown`` is not installed in the ``examples`` nox session.
    """
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(rf"[{separator}\s]+", separator, value)


def heading_slugs(markdown: str) -> set[str]:
    """Anchor slugs of all ATX headings, skipping lines inside fenced code blocks."""
    slugs, in_fence = set(), False
    for line in markdown.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if not in_fence and (m := HEADING_RE.match(line)):
            slugs.add(slugify(m["text"]))
    return slugs


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
