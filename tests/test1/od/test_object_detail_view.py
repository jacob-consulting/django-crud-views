import pytest
from django.template.loader import render_to_string

from crud_views_object_detail.lib.config import PropertyConfig
from crud_views_object_detail.lib.mixins import ObjectDetailMixin
from tests.test1.od_app.models import Info


@pytest.fixture
def mapped_detail(settings):
    from types import ModuleType

    from django.urls import path

    from tests.test1.app.models import Car, Truck
    from tests.test1.app.views import VehicleDetailView
    from tests.test1.project.urls import urlpatterns

    class MappedDetail(VehicleDetailView):
        cv_property_display = {
            Car: [{"title": "Car attributes", "properties": ["name", "doors"]}],
            Truck: [{"title": "Truck attributes", "properties": ["name", "payload_tons"]}],
        }

    urls = ModuleType("mapped_detail_urls")
    urls.urlpatterns = [path("mapped/<int:pk>/", MappedDetail.as_view()), *urlpatterns]
    settings.ROOT_URLCONF = urls
    return MappedDetail


@pytest.mark.django_db
class TestModelDisplayTracer:
    def test_mapped_car_request(self, mapped_detail, client_user_vehicle_view):
        from tests.test1.app.models import Car

        car = Car.objects.create(name="Mapped roadster", doors=3)
        # Assert the declaration is supported before exercising native dispatch/rendering.
        assert not {i for i in _error_ids(mapped_detail) if i.startswith("viewset.E24")}
        response = client_user_vehicle_view.get(f"/mapped/{car.pk}/")
        assert response.status_code == 200
        html = response.content.decode()
        assert "Car attributes" in html
        assert "Mapped roadster" in html
        assert "Doors" in html
        assert response.context["object_detail_groups"][0].properties[1].value == 3
        assert "Truck attributes" not in html

    def test_missing_exact_entry_names_model_and_view(self, mapped_detail, client_user_vehicle_view, monkeypatch):
        from django.core.exceptions import ImproperlyConfigured

        from tests.test1.app.models import Car

        car = Car.objects.create(name="Unmapped roadster")
        monkeypatch.setattr(mapped_detail, "cv_property_display", {})
        with pytest.raises(ImproperlyConfigured) as exc:
            client_user_vehicle_view.get(f"/mapped/{car.pk}/")
        assert "app.Car" in str(exc.value)
        assert f"{mapped_detail.__module__}.{mapped_detail.__qualname__}" in str(exc.value)


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


def test_property_group_config_entries_skip_dict_shape_checks():
    """A PropertyGroupConfig is already validated by pydantic, so E242-E245 must not
    fire for it, even next to a malformed dict group that does."""
    from crud_views_object_detail.lib.config import PropertyGroupConfig
    from crud_views_object_detail.lib.views import ObjectDetailView

    class V(ObjectDetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [
            PropertyGroupConfig(title="Typed", properties=["name"]),
            {"title": "Bad", "properties": [42]},
        ]

    messages = [m for chk in V.checks() for m in chk.messages()]
    ids = {m.id for m in messages}
    assert "viewset.E242" not in ids
    assert "viewset.E243" not in ids
    e245 = [m for m in messages if m.id == "viewset.E245"]
    assert len(e245) == 1, messages
    assert "cv_property_display[1]" in e245[0].msg, messages


def test_resolve_value_returns_list_when_single_path_fans_out_to_nothing():
    """First segment resolves, a later one is missing on every object: the result is
    an empty list, not _MISSING and not a single value."""
    from types import SimpleNamespace

    from crud_views_object_detail.lib.resolvers import _MISSING, _resolve_value

    obj = SimpleNamespace(child=SimpleNamespace())
    value = _resolve_value(obj, ["child", "absent"], is_many=False)
    assert value is not _MISSING
    assert value == []


@pytest.mark.parametrize("icon, flagged", [("xy:truck", True), ("fas:truck", False), ("truck", False), (None, False)])
def test_group_icon_unregistered_prefix_w246(icon, flagged):
    from crud_views_object_detail.lib.views import ObjectDetailView

    class V(ObjectDetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [{"title": "A", "icon": icon, "properties": ["name"]}]

    assert ("viewset.W246" in _error_ids(V)) is flagged


def test_group_icon_w246_for_property_group_config():
    from crud_views_object_detail.lib.config import PropertyGroupConfig
    from crud_views_object_detail.lib.views import ObjectDetailView

    class V(ObjectDetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [PropertyGroupConfig(title="A", icon="xy:truck", properties=["name"])]

    assert "viewset.W246" in _error_ids(V)


class TestModelDisplayChecks:
    @staticmethod
    def view(declaration):
        from crud_views_object_detail.lib.views import ObjectDetailView

        class DeclaredDetail(ObjectDetailView):
            cv_property_display = declaration
            cv_key = "detail"
            cv_path = "detail"

        return DeclaredDetail

    def test_every_entry_has_model_and_indices(self):
        from tests.test1.app.models import Author, Car, Truck

        view = self.view(
            {
                Author: [],
                Car: [{"title": "Car", "properties": [False]}],
                Truck: [{"properties": []}, {"title": "Truck", "properties": None}],
            }
        )
        messages = [m for chk in view.checks() for m in chk.messages()]
        errors = {m.id: m.msg for m in messages if m.id.startswith("viewset.E24")}
        assert "app.Car" in errors["viewset.E245"]
        assert "[0]['properties'][0]" in errors["viewset.E245"]
        assert "app.Truck" in errors["viewset.E242"]
        assert "[1]['properties']" in errors["viewset.E244"]
        assert all("DeclaredDetail" in message for message in errors.values())

    @pytest.mark.parametrize("key", ["bad", "{context}", 42, str, Info(pk=9)])
    def test_invalid_keys_still_check_values(self, key, monkeypatch):
        def forbidden(*args, **kwargs):
            raise AssertionError("Model instance must not be stringified")

        monkeypatch.setattr(Info, "__str__", forbidden)
        monkeypatch.setattr(Info, "__repr__", forbidden)
        view = self.view({key: [{"title": "Bad", "properties": [False]}]})
        checks = list(view.checks())
        messages = [m for chk in checks for m in chk.messages()]
        assert {"viewset.E247", "viewset.E245"} <= {m.id for m in messages}
        assert all("entry 0" in m.msg for m in messages if m.id in {"viewset.E247", "viewset.E245"})
        # Consumers may use the Check formatting API as well as messages().
        for chk in checks:
            if chk.id in {"E247", "E245"}:
                assert "entry 0" in chk.get_message()

    @pytest.mark.parametrize("value", [None, "groups", 1, {}, ()])
    @pytest.mark.parametrize("valid_key", [False, True])
    def test_invalid_value_shape(self, value, valid_key):
        key = Info if valid_key else "{invalid}"
        messages = [m for chk in self.view({key: value}).checks() for m in chk.messages()]
        errors = [m for m in messages if m.id == "viewset.E241"]
        assert len(errors) == 1
        assert (Info._meta.label if valid_key else "entry 0") in errors[0].msg
        assert ("viewset.E247" in {m.id for m in messages}) is not valid_key

    @pytest.mark.parametrize("group", [None, False, "bad", {}, {"title": "No properties"}])
    def test_malformed_groups(self, group):
        errors = _error_ids(self.view({Info: [group]}))
        assert "viewset.E243" in errors
        assert ("viewset.E242" in errors) is not (isinstance(group, dict) and "title" in group)

    @pytest.mark.parametrize("typed", [False, True])
    def test_nonfirst_icon_warning(self, typed):
        from crud_views_object_detail.lib.config import PropertyGroupConfig
        from tests.test1.app.models import Author

        group = {"title": "Bad icon", "icon": "xy:truck", "properties": ["text"]}
        if typed:
            group = PropertyGroupConfig(**group)
        messages = [m for chk in self.view({Author: [], Info: [group]}).checks() for m in chk.messages()]
        warning = next(m for m in messages if m.id == "viewset.W246")
        assert f"{Info._meta.label}][0]['icon']" in warning.msg

    @pytest.mark.django_db
    def test_checks_are_static_and_query_free(self, monkeypatch, django_assert_num_queries):
        from crud_views_object_detail.lib.config import PropertyGroupConfig

        view = self.view({Info: [PropertyGroupConfig(title="Info", properties=["text"])]})

        def forbidden(*args, **kwargs):
            raise AssertionError("Startup checks evaluated runtime state")

        monkeypatch.setattr(view, "__init__", forbidden)
        monkeypatch.setattr(view, "property_display", property(forbidden))
        monkeypatch.setattr(view, "get_object", forbidden)
        monkeypatch.setattr(view, "get_object_for_detail", forbidden)
        monkeypatch.setattr(Info, "__init__", forbidden)
        with django_assert_num_queries(0):
            assert not {i for i in _error_ids(view) if i.startswith("viewset.E24")}

    @pytest.mark.parametrize("declaration", [{}, {Info: []}, []])
    def test_empty_declarations(self, declaration):
        assert not {i for i in _error_ids(self.view(declaration)) if i.startswith("viewset.E24")}

    def test_none_outer_shape_and_inherited_checks(self):
        assert "viewset.E240" in _error_ids(self.view(None))
        assert "viewset.E241" in _error_ids(self.view("bad"))
        view = self.view({Info: []})
        view.cv_modal_size = "modal-huge"
        assert "viewset.E250" in _error_ids(view)


class TestModelDisplayCompatibility:
    @pytest.mark.parametrize("mapping_kind", ["defaultdict", "lookup_mapping"])
    @pytest.mark.parametrize("populated", [False, True])
    def test_default_producing_mapping_requires_declared_exact_key(self, mapping_kind, populated):
        from collections import defaultdict
        from collections.abc import Mapping
        from copy import deepcopy

        from django.core.exceptions import ImproperlyConfigured

        from tests.test1.app.models import Author

        factory_calls = []
        lookups = []

        def default_groups():
            factory_calls.append(True)
            return [{"title": "Undeclared fallback", "properties": []}]

        declared = {Info: [{"title": "Declared info", "properties": ["text"]}]} if populated else {}
        snapshot = deepcopy(declared)
        backing = defaultdict(default_groups, declared)

        class LookupMapping(Mapping):
            # Mapping.__contains__ delegates to __getitem__, so membership can create defaults too.
            def __getitem__(self, key):
                lookups.append(key)
                return backing[key]

            def __iter__(self):
                return iter(backing)

            def __len__(self):
                return len(backing)

        declaration = backing if mapping_kind == "defaultdict" else LookupMapping()

        class DeclaredDetail(ObjectDetailMixin):
            cv_property_display = declaration

        view = DeclaredDetail()
        view.object = Author()
        with pytest.raises(ImproperlyConfigured) as exc:
            view.get_property_display()
        assert "app.Author" in str(exc.value)
        assert f"{DeclaredDetail.__module__}.{DeclaredDetail.__qualname__}" in str(exc.value)
        assert factory_calls == []
        assert lookups == []
        assert DeclaredDetail.cv_property_display is declaration
        assert backing == snapshot

        if populated:
            view.object = Info(text="Declared value")
            selected = view.get_property_display()
            assert [group.title for group in selected] == ["Declared info"]
            assert selected[0].properties[0].path == "text"
            assert factory_calls == []
            assert lookups == ([Info] if mapping_kind == "lookup_mapping" else [])
            assert backing == snapshot

    @pytest.mark.django_db
    @pytest.mark.parametrize("mapped", [False, True])
    @pytest.mark.parametrize("forms", ["raw", "typed", "raw-typed", "typed-raw", "empty"])
    def test_group_forms(self, mapped, forms, django_assert_num_queries):
        from types import MappingProxyType

        from crud_views_object_detail.lib.config import PropertyGroupConfig

        raw = {"title": "Raw", "properties": ["text"]}
        typed = PropertyGroupConfig(title="Typed", properties=["text"])
        groups = {
            "raw": [raw],
            "typed": [typed],
            "raw-typed": [raw, typed],
            "typed-raw": [typed, raw],
            "empty": [],
        }[forms]
        view = ObjectDetailMixin()
        view.cv_property_display = MappingProxyType({Info: groups}) if mapped else groups
        if mapped:
            view.object = Info(text="A value")
        with django_assert_num_queries(0):
            selected = view.get_property_display()
        assert [g.title for g in selected] == [g["title"] if isinstance(g, dict) else g.title for g in groups]
        for original, result in zip(groups, selected, strict=True):
            if isinstance(original, PropertyGroupConfig):
                assert result is original
        assert raw == {"title": "Raw", "properties": ["text"]}

    def test_none_without_object(self):
        assert ObjectDetailMixin().get_property_display() == []

    def test_dynamic_override_reads_effective_property_once(self, rf):
        class DynamicDetail(ObjectDetailMixin):
            cv_property_display = {Info: [{"title": "Unused", "properties": []}]}
            reads = 0

            @property
            def property_display(self):
                self.reads += 1
                return [{"title": self.request.GET["title"], "properties": [self.object.text]}]

        view = DynamicDetail()
        view.object = Info(text="text")
        view.request = rf.get("/", {"title": "Dynamic title"})
        groups = view.get_property_display()
        assert view.reads == 1
        assert groups[0].title == "Dynamic title"
        assert groups[0].properties[0].path == "text"

    @pytest.mark.django_db
    def test_successive_requests_keep_declaration(self, mapped_detail, client_user_vehicle_view, monkeypatch):
        from copy import deepcopy

        from django.core.exceptions import ImproperlyConfigured

        from tests.test1.app.models import Car, Truck

        car = Car.objects.create(name="Roadster", doors=2)
        truck = Truck.objects.create(name="Hauler", payload_tons=17)
        declaration = mapped_detail.cv_property_display
        snapshot = deepcopy(declaration)
        for obj, title, absent, field, value in [
            (car, "Car attributes", "Truck attributes", "doors", 2),
            (truck, "Truck attributes", "Car attributes", "payload_tons", 17),
            (car, "Car attributes", "Truck attributes", "doors", 2),
        ]:
            response = client_user_vehicle_view.get(f"/mapped/{obj.pk}/")
            assert response.status_code == 200
            html = response.content.decode()
            assert title in html and absent not in html
            group = response.context["object_detail_groups"][0]
            assert [(p.path, p.value) for p in group.properties] == [("name", obj.name), (field, value)]
            assert mapped_detail.cv_property_display is declaration
            assert declaration == snapshot
        monkeypatch.setattr(mapped_detail, "cv_property_display", {Car: declaration[Car]})
        with pytest.raises(ImproperlyConfigured, match=r"app\.Truck"):
            client_user_vehicle_view.get(f"/mapped/{truck.pk}/")
