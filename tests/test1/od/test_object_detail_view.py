from crud_views_object_detail.lib.config import PropertyConfig


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
