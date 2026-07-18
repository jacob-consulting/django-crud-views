from django.test import override_settings

from crud_views_object_detail.lib.conf import CrudViewsObjectDetailSettings


class TestTemplatePackLayout:
    def test_default(self):
        assert CrudViewsObjectDetailSettings().template_pack_layout == "split-card"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT="accordion")
    def test_override(self):
        assert CrudViewsObjectDetailSettings().template_pack_layout == "accordion"


class TestTemplatePackTypes:
    def test_default(self):
        assert CrudViewsObjectDetailSettings().template_pack_types == "default"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES="custom")
    def test_override(self):
        assert CrudViewsObjectDetailSettings().template_pack_types == "custom"


class TestPropertyTextNewline:
    def test_default(self):
        assert CrudViewsObjectDetailSettings().property_text_newline == "linebreaksbr"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_PROPERTY_TEXT_NEWLINE="linebreaks")
    def test_override(self):
        assert CrudViewsObjectDetailSettings().property_text_newline == "linebreaks"
