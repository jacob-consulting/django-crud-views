import pytest
from django.contrib.contenttypes.models import ContentType
from django.test.client import Client
from django.urls import reverse

from crud_views.lib.viewset import ViewSet
from tests.lib.helper.boostrap5 import Table
from tests.test1.app.models import Car, Truck, Vehicle


@pytest.fixture
def library_delete_case(request, monkeypatch, settings):
    """Real library methods, isolated effect tables and a trusted same-alias router; restored per test."""
    from types import SimpleNamespace

    from django.db import connections, models
    from django.test.utils import isolate_apps

    from tests.test1.app.models import Author
    from tests.test1.app.views import AuthorDeleteView, VehicleDeleteView

    family, using = request.param
    model, view = (Author, AuthorDeleteView) if family == "author" else (Car, VehicleDeleteView)
    routes = []

    class Router:
        def db_for_read(self, candidate, **hints):
            if candidate._meta.app_label == "app":
                routes.append(("read", candidate, hints))
                return using

        def db_for_write(self, candidate, **hints):
            if candidate._meta.app_label == "app":
                routes.append(("write", candidate, hints))
                return using

    settings.DATABASE_ROUTERS = [Router()]
    if family == "author":
        from tests.test1.test_form_buttons_golden import AUTHOR_PK

        before = Author.objects.using(using).create(first_name="Before", last_name="Sibling")
        target = Author.objects.using(using).create(pk=AUTHOR_PK, first_name="Douglas", last_name="Adams")
        after = Author.objects.using(using).create(first_name="After", last_name="Sibling")
        siblings = [before, after]
        url = f"/author/{target.pk}/delete/"
        client = request.getfixturevalue("client_user_author_delete")
    else:
        target = Car.objects.using(using).create(name="Actual Car", doors=4)
        siblings = [Truck.objects.using(using).create(name="Untouched Truck", payload_tons=12)]
        url = f"/vehicle/{target.pk}/delete/"
        client = request.getfixturevalue("client_user_vehicle_delete")
    pk = target.pk
    sibling_rows = [type(row).objects.using(using).filter(pk=row.pk).values().get() for row in siblings]
    with isolate_apps("tests.test1.app"):

        class LibraryCascade(models.Model):
            target = models.ForeignKey(model, on_delete=models.CASCADE)

            class Meta:
                app_label = "app"

        class LibraryBlocker(models.Model):
            target = models.ForeignKey(model, on_delete=models.PROTECT)

            class Meta:
                app_label = "app"

        connection = connections[using]
        with connection.schema_editor() as editor:
            editor.create_model(LibraryCascade)
            editor.create_model(LibraryBlocker)
        try:
            with monkeypatch.context() as scope:
                original_fields = model._meta.get_fields
                relations = tuple(
                    effect._meta.get_field("target").remote_field for effect in (LibraryCascade, LibraryBlocker)
                )
                scope.setattr(
                    model._meta, "get_fields", lambda *args, **kwargs: (*original_fields(*args, **kwargs), *relations)
                )
                scope.setattr(view, "cv_show_related_objects", True)
                cascade = LibraryCascade.objects.using(using).create(target=target)
                case = SimpleNamespace(
                    family=family,
                    using=using,
                    model=model,
                    view=view,
                    target=target,
                    pk=pk,
                    client=client,
                    url=url,
                    siblings=siblings,
                    sibling_rows=sibling_rows,
                    cascade=cascade,
                    Cascade=LibraryCascade,
                    Blocker=LibraryBlocker,
                    routes=routes,
                    connection=connection,
                )
                yield case
        finally:
            with connection.schema_editor() as editor:
                editor.delete_model(LibraryBlocker)
                editor.delete_model(LibraryCascade)


def _exercise_actual_library_delete(case, monkeypatch, atomic, covered):
    from django.db.models.signals import post_delete, pre_delete

    from crud_views.lib.deletion import DeletePreviewContribution

    events, origins, updates = [], [], []
    original = case.model.delete

    def delete(self, *, using):
        assert using == case.using
        events.append("method")
        return original(self, using=using)

    def provider(self, boundaries, *, using):
        assert using == case.using
        assert len(boundaries) == 1 and boundaries[0].kind == "model_delete"
        return [DeletePreviewContribution(boundaries[0], complete=True)] if covered else []

    def success(self, context):
        assert case.connection.in_atomic_block is atomic
        assert not case.model.objects.using(case.using).filter(pk=case.pk).exists()
        assert not case.Cascade.objects.using(case.using).filter(pk=case.cascade.pk).exists()
        events.append("hook")

    def commit(self, context):
        assert case.connection.in_atomic_block is False
        events.append("commit")

    def receiver(sender, instance, origin, using, signal, **kwargs):
        assert using == case.using and type(origin) is case.model and origin.pk == case.pk
        origins.append((signal, sender, instance.pk, origin))

    def observe_sql(execute, sql, params, many, context):
        if sql.startswith("UPDATE") and "app_author" in sql:
            updates.append(context["connection"].alias)
        return execute(sql, params, many, context)

    monkeypatch.setattr(case.model, "delete", delete)
    monkeypatch.setattr(case.view, "cv_get_delete_preview", provider)
    monkeypatch.setattr(case.view, "cv_atomic", atomic)
    monkeypatch.setattr(case.view, "cv_form_valid_hook", success)
    monkeypatch.setattr(case.view, "cv_on_commit", commit)
    senders = [case.model, case.Cascade, *([Vehicle] if case.family == "car" else [])]
    for signal in (pre_delete, post_delete):
        for sender in senders:
            signal.connect(receiver, sender=sender, weak=False)
    try:
        for _ in range(2):
            response = case.client.get(case.url)
            assert response.status_code == 200
            assert response.context["delete_preview_incomplete"] is not covered
            assert response.context["has_protected_objects"] is False
            summary = {str(case.Cascade._meta.verbose_name): 1}
            if case.family == "car":
                summary[str(Vehicle._meta.verbose_name)] = 1
            assert response.context["related_summary"] == summary
            assert str(case.model._meta.verbose_name) not in summary
            assert events == origins == []
            content = response.content.decode()
            assert ("This preview is incomplete." in content) is not covered
            if not covered:
                assert content.index("This preview is incomplete.") < content.index('<form class="cv-form"')
            if case.family == "author":
                from tests.test1.test_form_buttons_golden import GOLDEN_DIR, _extract_controls, _golden_bytes

                assert (
                    _golden_bytes(_extract_controls(content, ("delete", "reset")))
                    == (GOLDEN_DIR / "delete.html").read_bytes()
                )
        assert case.client.post(case.url, {}).status_code == 200
        assert events == origins == []
        with case.connection.execute_wrapper(observe_sql):
            response = case.client.post(case.url, {"confirm": True})
        assert response.status_code == 302
    finally:
        for signal in (pre_delete, post_delete):
            for sender in senders:
                signal.disconnect(receiver, sender=sender)
    assert events == ["method", "hook", "commit"]
    assert len({id(origin) for *_, origin in origins}) == 1
    for sender in senders:
        assert [signal for signal, model, *_ in origins if model is sender] == [pre_delete, post_delete]
    assert not case.model.objects.using(case.using).filter(pk=case.pk).exists()
    assert not case.Cascade.objects.using(case.using).filter(pk=case.cascade.pk).exists()
    if case.family == "car":
        assert not Vehicle.objects.using(case.using).non_polymorphic().filter(pk=case.pk).exists()
        assert Truck.objects.using(case.using).filter(pk=case.siblings[0].pk).values().get() == case.sibling_rows[0]
    else:
        for index, sibling in enumerate(case.siblings):
            sibling.refresh_from_db(using=case.using)
            assert sibling.order == case.sibling_rows[index]["order"] - (1 if index else 0)
        assert updates == [case.using]
        assert any(
            kind == "write" and model is case.model and hints.get("instance") is not None
            for kind, model, hints in case.routes
        )


@pytest.mark.django_db(transaction=True, databases=["default", "shard"])
@pytest.mark.parametrize("library_delete_case", [("author", "default"), ("author", "shard")], indirect=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("covered", [False, True], ids=["partial", "safe-provider"])
def test_library_delete_author_reorders_and_remains_partial(library_delete_case, monkeypatch, atomic, covered):
    _exercise_actual_library_delete(library_delete_case, monkeypatch, atomic, covered)


@pytest.mark.django_db(transaction=True, databases=["default", "shard"])
@pytest.mark.parametrize("library_delete_case", [("car", "default"), ("car", "shard")], indirect=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("covered", [False, True], ids=["partial", "safe-provider"])
def test_library_delete_car_parent_rows_and_partial(library_delete_case, monkeypatch, atomic, covered):
    _exercise_actual_library_delete(library_delete_case, monkeypatch, atomic, covered)


@pytest.mark.django_db(transaction=True, databases=["default", "shard"])
@pytest.mark.parametrize("library_delete_case", [("author", "default"), ("car", "default")], indirect=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("stale", [False, True], ids=["known", "stale"])
@pytest.mark.parametrize("handler_name", ["PROTECT", "RESTRICT"])
def test_library_delete_native_protection_before_or_inside_override(
    library_delete_case, monkeypatch, atomic, stale, handler_name
):
    from django.db import models

    case = library_delete_case
    events, raised = [], []
    original = case.model.delete
    handler = getattr(models, handler_name)
    monkeypatch.setattr(case.Blocker._meta.get_field("target").remote_field, "on_delete", handler)
    monkeypatch.setattr(case.view, "cv_atomic", atomic)
    monkeypatch.setattr(case.view, "cv_form_valid_hook", lambda *args: events.append("hook"))
    monkeypatch.setattr(case.view, "cv_on_commit", lambda *args: events.append("commit"))

    def delete(self, *, using):
        assert using == case.using
        events.append("method")
        try:
            return original(self, using=using)
        except (models.ProtectedError, models.RestrictedError) as error:
            raised.append(error)
            raise

    def post_hook(self, context):
        assert context["has_protected_objects"] is False
        case.Blocker.objects.using(case.using).create(target=self.object)

    monkeypatch.setattr(case.model, "delete", delete)
    if not stale:
        case.Blocker.objects.using(case.using).create(target=case.target)
    response = case.client.get(case.url)
    assert response.status_code == 200
    assert response.context["delete_preview_incomplete"] is True
    assert response.context["has_protected_objects"] is not stale
    assert events == []
    if stale:
        # Insert after the actual safe inspection, before the write boundary: the real override encounters it.
        monkeypatch.setattr(case.view, "cv_post_hook", post_hook)
        error_type = models.ProtectedError if handler_name == "PROTECT" else models.RestrictedError
        with pytest.raises(error_type) as caught:
            case.client.post(case.url, {"confirm": True})
        assert caught.value is raised[0]
        assert events == ["method"]
    else:
        for data in ({}, {"confirm": True}):
            response = case.client.post(case.url, data)
            assert response.status_code == 200 and response.context["has_protected_objects"] is True
            assert "This preview is incomplete." in response.content.decode()
            assert "<form" not in response.content.decode()
        assert events == []
    assert case.model.objects.using(case.using).filter(pk=case.pk).exists()
    assert case.Cascade.objects.using(case.using).filter(pk=case.cascade.pk).exists()
    assert case.Blocker.objects.using(case.using).filter(target_id=case.pk).exists()
    if case.family == "author":
        for index, sibling in enumerate(case.siblings):
            sibling.refresh_from_db(using=case.using)
            reordered = index == 1 and stale and not atomic
            assert sibling.order == case.sibling_rows[index]["order"] - int(reordered)
    else:
        assert Vehicle.objects.using(case.using).non_polymorphic().filter(pk=case.pk).exists()


@pytest.mark.django_db(transaction=True, databases=["default", "shard"])
@pytest.mark.parametrize("library_delete_case", [("car", "default"), ("car", "shard")], indirect=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("failure", ["application", "protection"])
def test_library_delete_car_override_failure_propagates(library_delete_case, monkeypatch, atomic, failure):
    from django.db.models import ProtectedError

    case = library_delete_case
    error = (
        RuntimeError("subclass delete failed")
        if failure == "application"
        else ProtectedError("custom protection", {case.target})
    )
    events = []

    def delete(self, *, using):
        events.append(using)
        Car.objects.using(using).filter(pk=self.pk).update(doors=9)
        raise error

    monkeypatch.setattr(Car, "delete", delete)
    monkeypatch.setattr(case.view, "cv_atomic", atomic)
    monkeypatch.setattr(case.view, "cv_form_valid_hook", lambda *args: events.append("hook"))
    monkeypatch.setattr(case.view, "cv_on_commit", lambda *args: events.append("commit"))
    assert case.client.get(case.url).context["delete_preview_incomplete"] is True
    assert case.client.post(case.url, {}).status_code == 200
    assert events == []
    with pytest.raises(type(error)) as caught:
        case.client.post(case.url, {"confirm": True})
    assert caught.value is error
    assert events == [case.using]
    case.target.refresh_from_db(using=case.using)
    assert case.target.doors == (4 if atomic else 9)
    assert Vehicle.objects.using(case.using).non_polymorphic().filter(pk=case.pk).exists()
    assert case.Cascade.objects.using(case.using).filter(pk=case.cascade.pk).exists()


@pytest.mark.django_db
def test_library_delete_polymorphic_denied_never_inspects_or_calls_override(
    client_user_vehicle_view, car_sedan, monkeypatch
):
    from tests.test1.app.views import VehicleDeleteView

    def forbidden(*args, **kwargs):
        raise AssertionError("denied polymorphic requests must precede preview and deletion")

    monkeypatch.setattr(Car, "delete", forbidden)
    monkeypatch.setattr(VehicleDeleteView, "cv_get_delete_preview", forbidden)
    for method in ("get", "post", "delete"):
        response = getattr(client_user_vehicle_view, method)(f"/vehicle/{car_sedan.pk}/delete/", {"confirm": True})
        assert response.status_code == 403
    assert Car.objects.filter(pk=car_sedan.pk).exists()


@pytest.mark.django_db
def test_viewset_has_polymorphic_views(cv_vehicle: ViewSet):
    """Polymorphic viewset should have all expected views registered."""
    for view_name in ["list", "detail", "create", "create_select", "update", "delete"]:
        assert cv_vehicle.has_view(view_name), f"ViewSet missing view: {view_name}"


@pytest.mark.django_db
def test_viewset_url_patterns(cv_vehicle: ViewSet):
    """URL patterns should include polymorphic-specific routes."""
    routes = {p.name for p in cv_vehicle.urlpatterns}
    assert "vehicle-create_select" in routes
    assert "vehicle-create" in routes

    # Create URL should contain polymorphic_ctype_id
    create_patterns = [p for p in cv_vehicle.urlpatterns if p.name == "vehicle-create"]
    assert len(create_patterns) == 1
    assert "polymorphic_ctype_id" in create_patterns[0].pattern.regex.pattern


@pytest.mark.django_db
def test_list_shows_all_subtypes(client_user_vehicle_view: Client, cv_vehicle, car_sedan, truck_semi):
    """List view should show all polymorphic subtypes."""
    response = client_user_vehicle_view.get("/vehicle/")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 2
    names = {row.columns[1].text for row in table.rows}
    assert "Sedan" in names
    assert "Semi" in names


@pytest.mark.django_db
def test_detail_car(client_user_vehicle_view: Client, cv_vehicle, car_sedan):
    """Detail view should resolve to the correct polymorphic subtype."""
    response = client_user_vehicle_view.get(f"/vehicle/{car_sedan.pk}/detail/")
    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "Sedan" in content


@pytest.mark.django_db
def test_detail_truck(client_user_vehicle_view: Client, cv_vehicle, truck_semi):
    response = client_user_vehicle_view.get(f"/vehicle/{truck_semi.pk}/detail/")
    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "Semi" in content


@pytest.mark.django_db
def test_create_select_shows_form(client_user_vehicle_add: Client, cv_vehicle):
    """Create-select view should show a form with polymorphic type choices."""
    response = client_user_vehicle_add.get("/vehicle/create/select/")
    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "polymorphic_ctype_id" in content


@pytest.mark.django_db
def test_create_select_redirects_to_create(client_user_vehicle_add: Client, cv_vehicle):
    """Submitting create-select should redirect to the polymorphic create view."""
    car_ct = ContentType.objects.get_for_model(Car)
    response = client_user_vehicle_add.post("/vehicle/create/select/", {"polymorphic_ctype_id": car_ct.id})
    assert response.status_code == 302
    assert f"/vehicle/create/ct/{car_ct.id}/" in response.url


@pytest.mark.django_db
def test_create_car(client_user_vehicle_add: Client, cv_vehicle):
    """Creating a Car through the polymorphic create view."""
    car_ct = ContentType.objects.get_for_model(Car)

    # GET the form
    response = client_user_vehicle_add.get(f"/vehicle/create/ct/{car_ct.id}/")
    assert response.status_code == 200

    # POST the form
    response = client_user_vehicle_add.post(f"/vehicle/create/ct/{car_ct.id}/", {"name": "Coupe", "doors": 2})
    assert response.status_code == 302

    car = Car.objects.get(name="Coupe")
    assert car.doors == 2
    # Should also be queryable as Vehicle
    assert Vehicle.objects.filter(pk=car.pk).exists()


@pytest.mark.django_db
def test_create_legacy_double_slash_url_still_resolves(client_user_vehicle_add: Client, cv_vehicle):
    """URLs generated before 0.29.3 contained a double slash (create//ct/<id>/); keep them working."""
    car_ct = ContentType.objects.get_for_model(Car)
    response = client_user_vehicle_add.get(f"/vehicle/create//ct/{car_ct.id}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_create_url_has_no_double_slash(cv_vehicle):
    car_ct = ContentType.objects.get_for_model(Car)
    url = reverse(cv_vehicle.get_router_name("create"), kwargs={"polymorphic_ctype_id": car_ct.id})
    assert url == f"/vehicle/create/ct/{car_ct.id}/"


def test_create_default_context_actions_need_no_ctype():
    """The inherited "create" action can't be reversed without the content type, so it must not be a default."""
    from crud_views_polymorphic.lib import PolymorphicCreateView

    assert "create" not in PolymorphicCreateView.cv_context_actions


@pytest.mark.django_db
def test_create_truck(client_user_vehicle_add: Client, cv_vehicle):
    """Creating a Truck through the polymorphic create view."""
    truck_ct = ContentType.objects.get_for_model(Truck)

    response = client_user_vehicle_add.post(f"/vehicle/create/ct/{truck_ct.id}/", {"name": "Pickup", "payload_tons": 5})
    assert response.status_code == 302

    truck = Truck.objects.get(name="Pickup")
    assert truck.payload_tons == 5


@pytest.mark.django_db
def test_update_car(client_user_vehicle_change: Client, cv_vehicle, car_sedan):
    """Updating a Car through the polymorphic update view."""
    response = client_user_vehicle_change.get(f"/vehicle/{car_sedan.pk}/update/")
    assert response.status_code == 200

    response = client_user_vehicle_change.post(f"/vehicle/{car_sedan.pk}/update/", {"name": "Sports Car", "doors": 2})
    assert response.status_code == 302

    car_sedan.refresh_from_db()
    assert car_sedan.name == "Sports Car"
    assert car_sedan.doors == 2


@pytest.mark.django_db
def test_update_truck(client_user_vehicle_change: Client, cv_vehicle, truck_semi):
    """Updating a Truck through the polymorphic update view."""
    response = client_user_vehicle_change.post(
        f"/vehicle/{truck_semi.pk}/update/", {"name": "Big Rig", "payload_tons": 30}
    )
    assert response.status_code == 302

    truck_semi.refresh_from_db()
    assert truck_semi.name == "Big Rig"
    assert truck_semi.payload_tons == 30


@pytest.mark.django_db
def test_delete_vehicle(client_user_vehicle_delete: Client, cv_vehicle, car_sedan):
    """Deleting a polymorphic vehicle."""
    pk = car_sedan.pk

    response = client_user_vehicle_delete.get(f"/vehicle/{pk}/delete/")
    assert response.status_code == 200

    response = client_user_vehicle_delete.post(f"/vehicle/{pk}/delete/", {"confirm": True})
    assert response.status_code == 302

    assert not Vehicle.objects.filter(pk=pk).exists()
    assert not Car.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_delete_vehicle_http_delete_rejected(client_user_vehicle_delete: Client, cv_vehicle, car_sedan):
    """A26: the registered VehicleDeleteView inherits the DELETE rejection; Car and Vehicle rows stay intact."""
    pk = car_sedan.pk
    car_before = Car.objects.filter(pk=pk).values().get()
    vehicle_before = Vehicle.objects.non_polymorphic().filter(pk=pk).values().get()

    response = client_user_vehicle_delete.delete(f"/vehicle/{pk}/delete/")
    assert response.status_code == 405
    allow = {m.strip() for m in response.headers.get("Allow", "").split(",") if m.strip()}
    assert "DELETE" not in allow
    assert {"GET", "POST"} <= allow

    assert Car.objects.filter(pk=pk).values().get() == car_before
    assert Vehicle.objects.non_polymorphic().filter(pk=pk).values().get() == vehicle_before


@pytest.mark.django_db
def test_polymorphic_queryset_returns_subtypes(cv_vehicle, car_sedan, truck_semi):
    """Vehicle.objects.all() should return Car and Truck instances."""
    vehicles = list(Vehicle.objects.all())
    types = {type(v) for v in vehicles}
    assert Car in types
    assert Truck in types
