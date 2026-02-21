"""
Tests for DetailView.cv_property_display and checks().
"""

from django_object_detail import PropertyConfig


def _errors(view_cls):
    return [msg for chk in view_cls.checks() for msg in chk.messages()]


def _error_ids(view_cls):
    return {e.id for e in _errors(view_cls)}


# ---------------------------------------------------------------------------
# cv_property_display property adapter
# ---------------------------------------------------------------------------


def test_property_display_returns_cv_property_display():
    """property_display property returns cv_property_display."""
    from crud_views.lib.views.detail import DetailView

    class TestView(DetailView):
        cv_key = "detail"
        cv_property_display = [{"title": "A", "properties": ["x"]}]

    view = TestView()
    assert view.property_display == [{"title": "A", "properties": ["x"]}]


def test_property_display_none_when_not_set():
    """property_display returns None when cv_property_display is not overridden."""
    from crud_views.lib.views.detail import DetailView

    class TestView(DetailView):
        cv_key = "detail"

    view = TestView()
    assert view.property_display is None


# ---------------------------------------------------------------------------
# checks(): happy path
# ---------------------------------------------------------------------------


def test_detail_view_checks_pass():
    """A correctly configured DetailView produces no check errors."""
    from tests.test1.app.views import AuthorDetailView

    assert _errors(AuthorDetailView) == []


def test_detail_view_checks_pass_with_property_config():
    """cv_property_display containing PropertyConfig objects passes checks."""
    from tests.test1.app.views import CampaignDetailView

    assert _errors(CampaignDetailView) == []


# ---------------------------------------------------------------------------
# checks(): E240 — cv_property_display missing / None
# ---------------------------------------------------------------------------


def test_detail_view_checks_missing_cv_property_display():
    """cv_property_display=None yields E240."""
    from crud_views.lib.views.detail import DetailView

    class NoDisplayView(DetailView):
        cv_key = "detail"
        cv_path = "detail"
        # cv_property_display deliberately not set

    assert "viewset.E240" in _error_ids(NoDisplayView)


# ---------------------------------------------------------------------------
# checks(): E241 — not a list
# ---------------------------------------------------------------------------


def test_detail_view_checks_not_a_list():
    """cv_property_display that is not a list yields E241."""
    from crud_views.lib.views.detail import DetailView

    class BadTypeView(DetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = "not a list"

    assert "viewset.E241" in _error_ids(BadTypeView)


# ---------------------------------------------------------------------------
# checks(): E242 — group missing 'title'
# ---------------------------------------------------------------------------


def test_detail_view_checks_group_missing_title():
    """A group dict without 'title' yields E242."""
    from crud_views.lib.views.detail import DetailView

    class MissingTitleView(DetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [{"properties": ["x"]}]  # no 'title'

    assert "viewset.E242" in _error_ids(MissingTitleView)


# ---------------------------------------------------------------------------
# checks(): E243 — group missing 'properties'
# ---------------------------------------------------------------------------


def test_detail_view_checks_group_missing_properties():
    """A group dict without 'properties' yields E243."""
    from crud_views.lib.views.detail import DetailView

    class MissingPropsView(DetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [{"title": "A"}]  # no 'properties'

    assert "viewset.E243" in _error_ids(MissingPropsView)


# ---------------------------------------------------------------------------
# checks(): E244 — 'properties' not a list
# ---------------------------------------------------------------------------


def test_detail_view_checks_properties_not_a_list():
    """'properties' that is not a list yields E244."""
    from crud_views.lib.views.detail import DetailView

    class BadPropsView(DetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [{"title": "A", "properties": "not a list"}]

    assert "viewset.E244" in _error_ids(BadPropsView)


# ---------------------------------------------------------------------------
# checks(): E245 — invalid property type
# ---------------------------------------------------------------------------


def test_detail_view_checks_invalid_property_type():
    """A property that is not str, dict, or PropertyConfig yields E245."""
    from crud_views.lib.views.detail import DetailView

    class BadPropTypeView(DetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [{"title": "A", "properties": [42]}]

    assert "viewset.E245" in _error_ids(BadPropTypeView)


# ---------------------------------------------------------------------------
# checks(): valid variants accepted
# ---------------------------------------------------------------------------


def test_detail_view_checks_string_property_accepted():
    """Plain string properties pass E245."""
    from crud_views.lib.views.detail import DetailView

    class StringPropView(DetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [{"title": "A", "properties": ["name", "email"]}]

    assert "viewset.E245" not in _error_ids(StringPropView)


def test_detail_view_checks_dict_property_accepted():
    """Dict properties pass E245."""
    from crud_views.lib.views.detail import DetailView

    class DictPropView(DetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [{"title": "A", "properties": [{"path": "name", "detail": "The name"}]}]

    assert "viewset.E245" not in _error_ids(DictPropView)


def test_detail_view_checks_property_config_accepted():
    """PropertyConfig instances pass E245."""
    from crud_views.lib.views.detail import DetailView

    class PropertyConfigView(DetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [{"title": "A", "properties": [PropertyConfig(path="name")]}]

    assert "viewset.E245" not in _error_ids(PropertyConfigView)
