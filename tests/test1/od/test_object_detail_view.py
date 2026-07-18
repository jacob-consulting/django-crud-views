from django.template.loader import render_to_string

from crud_views_object_detail.lib.config import PropertyConfig
from crud_views_object_detail.lib.mixins import ObjectDetailMixin
from tests.test1.od_app.models import Info


def _error_ids(view_cls):
    return {e.id for chk in view_cls.checks() for e in chk.messages()}


def test_object_detail_view_property_display_adapter():
    from crud_views_object_detail.lib.views import ObjectDetailView

    class V(ObjectDetailView):
        cv_key = "detail"
        cv_property_display = [{"title": "A", "properties": ["x"]}]

    assert V().property_display == [{"title": "A", "properties": ["x"]}]


def test_object_detail_view_missing_display_yields_e240():
    from crud_views_object_detail.lib.views import ObjectDetailView

    class V(ObjectDetailView):
        cv_key = "detail"
        cv_path = "detail"

    assert "viewset.E240" in _error_ids(V)


def test_object_detail_view_property_config_accepted():
    from crud_views_object_detail.lib.views import ObjectDetailView

    class V(ObjectDetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [{"title": "A", "properties": [PropertyConfig(path="name")]}]

    assert "viewset.E245" not in _error_ids(V)


def test_object_detail_view_checks_chain_base_crud_view_checks():
    """ObjectDetailMixin.checks() must yield from super().checks() so base CrudView
    checks (E200/E201/E111/E250/E251) still fire. cv_property_display is well-formed
    here (no E240-E245), and cv_modal_size is deliberately invalid to force the base
    CrudView.checks() E250 check to fire, proving it propagates through the mixin's
    super() chain.
    """
    from crud_views_object_detail.lib.views import ObjectDetailView

    class V(ObjectDetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [{"title": "A", "properties": [PropertyConfig(path="name")]}]
        cv_modal_size = "modal-huge"

    error_ids = _error_ids(V)
    assert "viewset.E240" not in error_ids
    assert "viewset.E245" not in error_ids
    assert "viewset.E250" in error_ids


# ---------------------------------------------------------------------------
# cv_object_detail_layout — per-view layout override
# ---------------------------------------------------------------------------


class _StubDetailBase:
    """Stands in for crud_views' DetailView so ObjectDetailMixin can be tested without
    the full CrudView/ViewSet stack (no url routing, no request needed)."""

    def get_context_data(self, **kwargs):
        return {}


def test_object_detail_mixin_layout_override_defaults_to_none():
    """cv_object_detail_layout defaults to None (i.e. defer to the global settings pack)."""

    class V(ObjectDetailMixin, _StubDetailBase):
        cv_property_display = [{"title": "General", "properties": ["text"]}]

        def get_object_for_detail(self):
            return Info(text="Widget")

    context = V().get_context_data()
    assert context["object_detail_layout"] is None


def test_object_detail_mixin_layout_override_threaded_into_context():
    """cv_object_detail_layout, when set, lands in the context as object_detail_layout."""

    class V(ObjectDetailMixin, _StubDetailBase):
        cv_object_detail_layout = "accordion"
        cv_property_display = [{"title": "General", "properties": ["text"]}]

        def get_object_for_detail(self):
            return Info(text="Widget")

    context = V().get_context_data()
    assert context["object_detail_layout"] == "accordion"


def test_view_with_layout_override_renders_accordion_marker():
    """End-to-end: a view with cv_object_detail_layout="accordion" must render the
    accordion pack's discriminating marker (accordion-item) even though the test
    settings' global default pack is "split-card" (see tests/test1/od/conftest.py /
    conf.py default). This proves the per-view override propagates all the way through
    view_detail.content.html -> render_object_detail -> render_group -> render_property.
    """

    class V(ObjectDetailMixin, _StubDetailBase):
        cv_object_detail_layout = "accordion"
        cv_property_display = [{"title": "General", "properties": ["text"]}]

        def get_object_for_detail(self):
            return Info(text="Widget")

    view = V()
    context = view.get_context_data()
    context["object"] = Info(text="Widget")
    html = render_to_string("crud_views_object_detail/view_detail.content.html", context)
    assert "accordion-item" in html
