"""System check viewset.E255: context buttons whose target view or ViewSet does not resolve (issue #172)."""

import pytest

from crud_views.lib.view import ChildContextButton, ContextButton, ParentContextButton, SiblingContextButton
from crud_views.lib.view.buttons import FilterContextButton
from crud_views.lib.viewset import ViewSet, context_buttons_default

E255 = "viewset.E255"


def vs(name: str) -> ViewSet:
    import tests.test1.app.views  # noqa: F401 -- populates the ViewSet registry

    return ViewSet.get_viewset(name)


def e255_messages(checks) -> list[str]:
    return [m.msg for c in checks for m in c.messages() if m.id == E255]


def viewset_e255(viewset: ViewSet, buttons: list) -> list[str]:
    # model_copy skips the registering validator but keeps the registered views
    return e255_messages(viewset.model_copy(update={"context_buttons": buttons}).checks())


# ---------------------------------------------------------------------------
# cv_check_target: per-button resolution
# ---------------------------------------------------------------------------


def test_child_button_resolves():
    assert ChildContextButton(key="books", child_name="book").cv_check_target(vs("publisher")) is None


def test_child_button_unknown_viewset():
    problem = ChildContextButton(key="books", child_name="bok").cv_check_target(vs("publisher"))
    assert "'books'" in problem and "ChildContextButton" in problem and "'bok'" in problem


def test_child_button_unknown_key():
    problem = ChildContextButton(key="books", child_name="book", child_key="lsit").cv_check_target(vs("publisher"))
    assert "'lsit'" in problem and "'book'" in problem


def test_child_button_not_a_child():
    problem = ChildContextButton(key="authors", child_name="author").cv_check_target(vs("publisher"))
    assert "'author'" in problem and "child" in problem


def test_sibling_button_resolves():
    assert SiblingContextButton(key="contracts", sibling_name="contract").cv_check_target(vs("book")) is None


def test_sibling_button_unknown_viewset():
    problem = SiblingContextButton(key="contracts", sibling_name="contrakt").cv_check_target(vs("book"))
    assert "'contrakt'" in problem and "SiblingContextButton" in problem


def test_sibling_button_unknown_key():
    btn = SiblingContextButton(key="contracts", sibling_name="contract", sibling_key="update")
    problem = btn.cv_check_target(vs("book"))
    assert "'update'" in problem and "'contract'" in problem


def test_sibling_button_list_falls_back_to_card():
    btn = SiblingContextButton(key="cards", sibling_name="author_wide_card")
    assert btn.cv_check_target(vs("book")) is None


def test_parent_button_resolves():
    assert ParentContextButton(key="up", key_target="detail").cv_check_target(vs("book")) is None


def test_parent_button_unknown_key():
    problem = ParentContextButton(key="up", key_target="detial").cv_check_target(vs("book"))
    assert "'detial'" in problem and "'publisher'" in problem and "ParentContextButton" in problem


def test_parent_button_without_parent():
    problem = ParentContextButton(key="up", key_target="list").cv_check_target(vs("publisher"))
    assert "'up'" in problem and "parent" in problem


def test_plain_button_resolves():
    assert ContextButton(key="edit", key_target="update").cv_check_target(vs("book")) is None


def test_plain_button_unknown_key():
    problem = ContextButton(key="edit", key_target="updte").cv_check_target(vs("book"))
    assert "'edit'" in problem and "ContextButton" in problem and "'updte'" in problem


def test_plain_button_list_falls_back_to_card():
    assert ContextButton(key="cards", key_target="list").cv_check_target(vs("author_wide_card")) is None


def test_plain_button_without_target_is_skipped():
    assert ContextButton(key="custom").cv_check_target(vs("book")) is None


def test_button_overriding_get_context_is_skipped():
    class CustomButton(ContextButton):
        def get_context(self, context):
            return {}

    assert CustomButton(key="custom", key_target="nope").cv_check_target(vs("book")) is None
    assert FilterContextButton().cv_check_target(vs("book")) is None


# ---------------------------------------------------------------------------
# ViewSet-level context_buttons
# ---------------------------------------------------------------------------


def test_viewset_reports_unresolved_button():
    messages = viewset_e255(vs("publisher"), [ChildContextButton(key="books", child_name="book", child_key="lsit")])
    assert len(messages) == 1
    assert "'lsit'" in messages[0] and "publisher" in messages[0]


def test_viewset_defaults_are_not_flagged():
    # "home" -> list on a detail-only ViewSet (#132) and "parent" on a root ViewSet
    assert viewset_e255(vs("author_detail_only"), context_buttons_default()) == []


def test_viewset_default_lookalike_is_not_flagged():
    buttons = [ContextButton(key="home", key_target="list"), ParentContextButton(key="parent", key_target="list")]
    assert viewset_e255(vs("author_detail_only"), buttons) == []


def test_registered_viewsets_have_no_e255():
    vs("publisher")
    assert e255_messages(ViewSet.checks_all()) == []


# ---------------------------------------------------------------------------
# view-level cv_context_buttons
# ---------------------------------------------------------------------------


def test_view_level_unresolved_button():
    from tests.test1.app.views import PublisherDetailView

    class Probe(PublisherDetailView):  # no cv_viewset in attrs -> not registered
        cv_context_buttons = [ChildContextButton(key="books", child_name="book", child_key="lsit")]

    messages = e255_messages(Probe.checks())
    assert len(messages) == 1
    assert "'lsit'" in messages[0]


def test_view_level_resolved_button():
    from tests.test1.app.views import PublisherDetailView

    class Probe(PublisherDetailView):
        cv_context_buttons = [ChildContextButton(key="books", child_name="book")]

    assert e255_messages(Probe.checks()) == []


def test_view_level_without_viewset_is_skipped():
    from crud_views.lib.views import DetailView

    class Unbound(DetailView):
        cv_context_buttons = [ContextButton(key="edit", key_target="nope")]

    assert e255_messages(Unbound.checks()) == []


@pytest.mark.parametrize("key", ["home", "parent"])
def test_view_level_defaults_are_not_flagged(key):
    from tests.test1.app.views import AuthorDetailOnlyView

    class Probe(AuthorDetailOnlyView):
        cv_context_buttons = [b for b in context_buttons_default() if b.key == key]

    assert e255_messages(Probe.checks()) == []
