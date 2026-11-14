from functools import cached_property

from crud_views.lib.check import CheckUnknownAttributes
from crud_views.lib.view.base import CrudView

# Bare CrudView subclasses do NOT register (metaclass registers only when
# cv_viewset is in the class body), so these are safe, unregistered fixtures
# whose MRO still includes the package classes that populate the known-set.


class DeadAttrView(CrudView):
    cv_message = "Created {{ object }}"  # dead: real API is cv_message_template_code


class GoodOverrideView(CrudView):
    cv_message_template_code = "Created {{ object }}"  # legitimate override of a known attr


class MethodView(CrudView):
    def cv_helper(self):  # user cv_* method — not a data attribute, must not warn
        return 1

    @property
    def cv_computed(self):  # descriptor — must not warn
        return 2

    @cached_property
    def cv_cached(self):  # descriptor — must not warn
        return 3


class ExemptView(CrudView):
    cv_check_ignore_attributes = frozenset({"cv_custom"})
    cv_custom = 1  # custom data attr, exempted by the allowlist


class UnexemptView(CrudView):
    cv_custom = 1  # same custom data attr, but NOT exempted -> must warn


class _ExemptMixin(CrudView):
    cv_check_ignore_attributes = frozenset({"cv_from_mixin"})
    cv_from_mixin = 1


class UnionExemptView(_ExemptMixin):
    cv_check_ignore_attributes = frozenset({"cv_from_leaf"})
    cv_from_leaf = 2


class MethodShadowView(CrudView):
    cv_get_message = "literal"  # shadows a real package METHOD name with data — known name, must not warn


def _w280(context):
    return list(CheckUnknownAttributes(context=context).messages())


def test_dead_attribute_warns_and_suggests_near_match():
    messages = _w280(DeadAttrView)
    assert len(messages) == 1
    m = messages[0]
    assert m.id == "viewset.W280"
    assert "cv_message" in m.msg
    # cv_message_template and cv_message_template_code are both valid near-matches;
    # "cv_message_template" is a substring of both, so this tolerates either suggestion.
    assert "cv_message_template" in m.msg
    # Suggestion pool is context-local: an ActionView-only attribute (in the package-wide
    # detection set but not in a plain CrudView's MRO) must never be suggested here.
    assert "cv_action_messages" not in m.msg


def test_legitimate_override_does_not_warn():
    assert _w280(GoodOverrideView) == []


def test_cv_methods_and_descriptors_do_not_warn():
    assert _w280(MethodView) == []


def test_allowlisted_custom_attribute_does_not_warn():
    assert _w280(ExemptView) == []


def test_unlisted_custom_attribute_warns():
    messages = _w280(UnexemptView)
    assert len(messages) == 1
    assert "cv_custom" in messages[0].msg


def test_allowlist_is_unioned_across_the_mro():
    # If the check used getattr (leaf shadows), cv_from_mixin would leak a warning.
    assert _w280(UnionExemptView) == []


def test_shadowing_a_known_method_name_with_data_does_not_warn():
    assert _w280(MethodShadowView) == []


def test_annotation_only_package_attribute_is_known():
    # cv_formsets is declared annotation-only (no default) on FormSetMixin; a view that
    # legitimately sets it must not be flagged as unknown (regression for the vars()-only gap).
    from crud_views.lib.formsets.mixins import FormSetMixin

    class FormsetUserView(FormSetMixin, CrudView):
        cv_formsets = "sentinel"  # value type is irrelevant to the name-based known-set

    assert _w280(FormsetUserView) == []


def test_real_package_attr_on_view_without_its_mixin_is_not_flagged():
    # cv_formsets is a real package attribute (FormSetMixin) read generically by check_conditional.
    # A registered formset view puts it in the package vocabulary, so setting it on a view that
    # does NOT inherit FormSetMixin must not be flagged (package-wide known-set, not MRO-local).
    # Importing the module registers PublisherFormSet* views, so this holds regardless of the
    # test execution order / scope (in-process, the registry is otherwise import-order dependent).
    import tests.test1.app.views_formset  # noqa: F401 — ensures a FormSetMixin view is registered

    class PlainView(CrudView):
        cv_formsets = "sentinel"

    assert _w280(PlainView) == []


def test_checks_chain_yields_the_unknown_attribute_check():
    ids = [c.id for c in DeadAttrView.checks()]
    assert "W280" in ids


def test_checks_chain_emits_w280_for_dead_attr():
    warnings = [m for c in DeadAttrView.checks() for m in c.messages() if getattr(m, "id", None) == "viewset.W280"]
    assert any("cv_message" in w.msg for w in warnings)


def test_registered_views_have_no_unknown_attribute_warnings():
    # Guards against false positives on the real, correctly-configured test-app views.
    from crud_views.lib.viewset import ViewSet

    w280 = [m for c in ViewSet.checks_all() for m in c.messages() if getattr(m, "id", None) == "viewset.W280"]
    assert w280 == [], [w.msg for w in w280]


def test_checks_all_releases_registry_lock_before_yielding():
    # Regression: checks_all() must snapshot-then-release _REGISTRY_LOCK. If it holds the lock
    # across yields, calling .messages() on a yielded check (which re-acquires the lock via the
    # package-wide vocabulary) self-deadlocks. Probe: the lock must be free during iteration.
    from crud_views.lib.viewset import _REGISTRY_LOCK, ViewSet

    for _check in ViewSet.checks_all():
        acquired = _REGISTRY_LOCK.acquire(blocking=False)
        if acquired:
            _REGISTRY_LOCK.release()
        assert acquired, "checks_all() held _REGISTRY_LOCK across a yield — messages() would deadlock"
        break


class RemovedParentKeyView(CrudView):
    cv_parent_key = "list"  # removed (issue #74): it never had an effect


def test_removed_cv_parent_key_warns():
    messages = _w280(RemovedParentKeyView)
    assert [m.id for m in messages] == ["viewset.W280"]
    assert "cv_parent_key" in messages[0].msg


def test_diagnostic_class_discovery_does_not_broaden_w280():
    from crud_views.lib.check import _collect_cv_names, _project_cv_declarations

    class Explosive:
        def __get__(self, instance, owner=None):
            raise AssertionError("Diagnostics must not evaluate descriptors")

    class ProjectView(CrudView):
        cv_custom_class = dict
        cv_custom_descriptor = Explosive()
        cv_custom_property = property(lambda self: 1)
        cv_custom_method = staticmethod(lambda: 1)
        cv_custom_data = 1
        cv_check_ignore_attributes = {"cv_custom_data"}

    all_names, data_names = set(), set()
    _collect_cv_names(ProjectView, all_names, data_names)
    assert "cv_custom_class" not in data_names
    _collect_cv_names(ProjectView, all_names, data_names, include_classes=True)
    assert "cv_custom_class" in data_names
    assert not {"cv_custom_descriptor", "cv_custom_property", "cv_custom_method"} & data_names
    assert "cv_custom_class" in _project_cv_declarations(ProjectView, include_classes=True)
    assert _w280(ProjectView) == []


def test_package_prefix_stays_library_for_unknown_discovery():
    class ThemeView(CrudView):
        cv_theme_only = 1

    ThemeView.__module__ = "crud_views_theme.views"
    assert _w280(ThemeView) == []
