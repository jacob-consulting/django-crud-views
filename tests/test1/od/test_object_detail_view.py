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
