import re
from types import ModuleType, SimpleNamespace

import pytest
from django.test.client import Client

from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def protected_destination(
    monkeypatch, settings, publisher_penguin, user_publisher_cascade_delete, cv_publisher_cascade
):
    """A real registered destination with an isolated registry and URLconf."""
    from django.contrib.auth.models import Permission
    from django.http import HttpResponse
    from django.test import RequestFactory
    from django.urls import clear_url_caches, path

    from crud_views.lib.views import DetailViewPermissionRequired
    from crud_views.lib.viewset import _REGISTRY, ViewSet
    from tests.test1.app.models import Contract

    monkeypatch.setattr(
        "crud_views.lib.viewset._REGISTRY",
        {name: viewset for name, viewset in _REGISTRY.items() if viewset.model is not Contract},
    )
    viewset = ViewSet(model=Contract, name="protected_destination", prefix="protected_destination")

    class Detail(DetailViewPermissionRequired):
        cv_viewset = viewset
        template_name = "crud_views/view_detail.html"

        def render_to_response(self, context, **kwargs):
            return HttpResponse(f"contract:{self.object.pk}")

    blocker = Contract.objects.create(title="Visible blocker", publisher=publisher_penguin)
    user_publisher_cascade_delete.user_permissions.add(Permission.objects.get(codename="view_contract"))
    patterns = [*cv_publisher_cascade.urlpatterns, *viewset.urlpatterns]
    urlconf = ModuleType("protected_destination_urls")
    urlconf.urlpatterns = patterns
    settings.ROOT_URLCONF = urlconf
    request = RequestFactory().post("/source/?original=yes", {"confirm": "true"}, HTTP_X_CV_MODAL="true")
    request.user = user_publisher_cascade_delete
    request.urlconf = urlconf
    request.session = {"kept": True}
    source = cv_publisher_cascade.get_view_class("delete")()
    source.setup(request, pk=publisher_penguin.pk)
    source.object = publisher_penguin
    source.cv_link_related_objects = True
    url = f"/protected_destination/{blocker.pk}/detail/"

    # Use explicit routes for native lookup/initkwarg variants alongside registered routes.
    def route(callback, route="candidate/<int:pk>/"):
        patterns.append(path(route, callback))
        clear_url_caches()

    yield SimpleNamespace(source=source, target=Detail, blocker=blocker, url=url, route=route, patterns=patterns)
    clear_url_caches()


@pytest.mark.django_db
@pytest.mark.parametrize("permitted", [True, False])
def test_protected_link_request_tracer(
    protected_destination, client_user_publisher_cascade_delete, monkeypatch, permitted
):
    from html.parser import HTMLParser

    case = protected_destination
    source_class = type(case.source)
    monkeypatch.setattr(source_class, "cv_link_related_objects", True)
    monkeypatch.setattr(case.target, "cv_has_access", classmethod(lambda cls, user, obj=None: permitted))
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{case.source.object.pk}/delete/")
    assert response.status_code == 200
    expected = case.url if permitted else None
    assert response.context["protected_objects"] == [{"obj": case.blocker, "url": expected}]

    class Anchors(HTMLParser):
        hrefs = []

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                self.hrefs.append(dict(attrs).get("href"))

    parser = Anchors()
    parser.feed(response.content.decode())
    if permitted:
        assert case.url in parser.hrefs
        followed = client_user_publisher_cascade_delete.get(case.url)
        assert followed.status_code == 200
        assert followed.content.decode() == f"contract:{case.blocker.pk}"
    else:
        assert case.url not in parser.hrefs
        assert "Visible blocker" in response.content.decode()
    assert "<form" not in response.content.decode()
    case.blocker.refresh_from_db()
    case.source.object.refresh_from_db()


@pytest.mark.django_db
@pytest.mark.parametrize("policy", ["allowed", "permission", "state", "queryset", "missing-detail", "missing-route"])
def test_protected_target_policy_matrix(protected_destination, monkeypatch, policy):
    from django.urls import clear_url_caches

    from tests.test1.app.models import Contract

    case = protected_destination
    source_calls, target_calls = [], []
    monkeypatch.setattr(type(case.source), "cv_action_enabled", classmethod(lambda *a: source_calls.append(a) or True))
    monkeypatch.setattr(
        case.target, "cv_action_enabled", classmethod(lambda *a: target_calls.append(a) or policy != "state")
    )
    if policy == "permission":
        monkeypatch.setattr(case.target, "cv_has_access", classmethod(lambda *a: False))
    if policy == "queryset":
        monkeypatch.setattr(case.target, "get_queryset", lambda self: Contract.objects.none())
    if policy == "missing-detail":
        monkeypatch.setattr(type(case.target.cv_viewset), "is_view_registered", lambda self, key: False)
    if policy == "missing-route":
        case.patterns.clear()
        clear_url_caches()
    assert case.source._cv_get_protected_object_url(case.blocker) == (case.url if policy == "allowed" else None)
    assert source_calls == []
    assert len(target_calls) == int(policy in {"allowed", "state"})
    if policy == "allowed":
        client = Client()
        client.force_login(case.source.request.user)
        assert client.get(case.url).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("method,modal", [("get", False), ("get", True), ("post", True)])
def test_protected_target_binding(protected_destination, monkeypatch, method, modal):
    from django.test import RequestFactory

    case = protected_destination
    original_actor = case.source.request.user
    request = getattr(RequestFactory(), method)("/source/?original=yes", HTTP_X_CV_MODAL="true" if modal else "")
    request.user = original_actor
    request.urlconf = case.source.request.urlconf
    case.source.request = request
    source_snapshot = (request.META.copy(), request.GET.copy(), request.POST.copy(), case.source.kwargs.copy())
    candidate = case.url + "?q=caf%C3%A9&q=two#résumé"
    monkeypatch.setattr(case.source, "cv_get_related_object_url", lambda obj: candidate)
    calls = []

    def queryset(self):
        calls.append(self)
        assert self.request.method == "GET"
        assert self.request.GET.getlist("q") == ["café", "two"]
        assert self.request.POST == {}
        assert "X-CV-Modal" not in self.request.headers
        assert self.request.path == case.url
        assert self.request.resolver_match.func.view_class is case.target
        assert self.kwargs == self.request.resolver_match.kwargs
        assert int(self.kwargs["pk"]) == case.blocker.pk
        return type(case.blocker).objects.all()

    monkeypatch.setattr(case.target, "get_queryset", queryset)
    for _ in range(2):
        assert case.source._cv_get_protected_object_url(case.blocker) == candidate
    assert calls[0] is not calls[1]
    assert (request.META, request.GET, request.POST, case.source.kwargs) == source_snapshot
    assert request.user is original_actor


@pytest.mark.django_db
@pytest.mark.parametrize("override", ["dispatch", "get_object"])
def test_protected_custom_request_remains_authoritative(protected_destination, monkeypatch, override):
    from django.core.exceptions import PermissionDenied

    case = protected_destination
    called = []

    def deny(*args, **kwargs):
        called.append(override)
        raise PermissionDenied

    monkeypatch.setattr(case.target, override, deny)
    assert case.source._cv_get_protected_object_url(case.blocker) == case.url
    assert called == []
    client = Client()
    client.force_login(case.source.request.user)
    assert client.get(case.url).status_code == 403
    assert called == [override]


@pytest.mark.django_db
@pytest.mark.parametrize("allowed", [False, True])
def test_protected_override_uses_actual_registered_target(protected_destination, monkeypatch, allowed):
    from django.urls import clear_url_caches

    from crud_views.lib.viewset import ViewSet

    case = protected_destination
    alternate = ViewSet(model=type(case.blocker), name="alternate_protected_target")

    class Alternate(case.target):
        cv_viewset = alternate

        @classmethod
        def cv_action_enabled(cls, user, obj=None):
            return allowed

    case.patterns.extend(alternate.urlpatterns)
    clear_url_caches()
    url = f"/alternate_protected_target/{case.blocker.pk}/detail/"
    monkeypatch.setattr(case.source, "cv_get_related_object_url", lambda obj: url)
    # The first/default registered target must not substitute its own state policy.
    monkeypatch.setattr(case.target, "cv_action_enabled", classmethod(lambda *args: not allowed))
    assert case.source._cv_get_protected_object_url(case.blocker) == (url if allowed else None)
    client = Client()
    client.force_login(case.source.request.user)
    assert client.get(url).status_code == (200 if allowed else 403)


@pytest.mark.django_db
def test_protected_source_state_only_normal_request(
    protected_destination, client_user_publisher_cascade_delete, monkeypatch
):
    case = protected_destination
    source = type(case.source)
    native = source.cv_action_enabled.__func__
    source_calls, target_calls = [], []

    def state(cls, user, obj=None):
        source_calls.append(obj)
        return native(cls, user, obj)

    monkeypatch.setattr(source, "cv_action_enabled", classmethod(state))
    monkeypatch.setattr(case.target, "cv_action_enabled", classmethod(lambda *args: target_calls.append(args) or True))
    counts = []
    for enabled in (False, True):
        source_calls.clear()
        monkeypatch.setattr(source, "cv_link_related_objects", enabled)
        response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{case.source.object.pk}/delete/")
        assert response.status_code == 200
        counts.append(len(source_calls))
    assert counts[0] >= 1
    assert counts[0] == counts[1]
    assert len(target_calls) == 1


@pytest.mark.django_db
def test_protected_uuid_identity(protected_destination, author_douglas_adams, cv_author, monkeypatch):
    from django.contrib.auth.models import Permission
    from django.urls import clear_url_caches

    case = protected_destination
    case.patterns.extend(cv_author.urlpatterns)
    clear_url_caches()
    case.source.request.user.user_permissions.add(Permission.objects.get(codename="view_author"))
    row = author_douglas_adams
    url = case.source.cv_get_related_object_url(row)
    assert str(row.pk) in url
    assert case.source._cv_get_protected_object_url(row) == url
    client = Client()
    client.force_login(case.source.request.user)
    assert client.get(url).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    "candidate",
    [
        None,
        "",
        "https://evil.test/",
        "//evil.test/",
        "relative/",
        "\n/candidate/1/",
        "/a\\b/",
        "/%2f/evil.test",
        "/%2F%2fevil.test",
        "/%5c",
        "/%00",
        "/%0a",
        "/%0D",
        "/%ff/",
        "/missing/",
    ],
)
def test_protected_candidate_contract_unsafe(protected_destination, monkeypatch, candidate):
    case = protected_destination
    monkeypatch.setattr(case.source, "cv_get_related_object_url", lambda obj: candidate)
    monkeypatch.setattr(case.target, "get_queryset", lambda self: pytest.fail("Unsafe URL reached target"))
    # The fallback makes RED an assertion about the missing contract, not an AttributeError.
    adapter = getattr(case.source, "_cv_get_protected_object_url", case.source.cv_get_related_object_url)
    assert adapter(case.blocker) is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "branch",
    [
        "valid",
        "query-fragment",
        "presentation",
        "denied",
        "disabled",
        "permission-denied",
        "missing-row",
        "queryset-404",
        "queryset-get-404",
        "queryset-error",
        "hook-404",
        "hook-reverse",
        "policy-404",
        "policy-error",
        "cv-override",
        "permission-override",
        "method-override",
        "non-detail",
        "unregistered",
        "wrong-row",
        "lookup-kwarg",
        "slug",
        "pk-and-slug",
        "wrong-slug",
        "missing-coordinate",
        "unicode",
        "wrong-model",
        "queryset-init",
    ],
)
def test_protected_candidate_contract(protected_destination, monkeypatch, branch):
    from django.core.exceptions import PermissionDenied
    from django.http import Http404, HttpResponse
    from django.urls import NoReverseMatch
    from django.views.generic.detail import SingleObjectMixin

    from tests.test1.app.models import Contract, Publisher

    case = protected_destination
    target = case.target
    candidate = case.url
    expected = True
    error = None
    calls = []

    def fail(exc):
        def raising(*args, **kwargs):
            raise exc

        return raising

    def available(cls, user, obj, view):
        calls.append(view)
        assert view.request.method == "GET"
        assert view.request.POST == {}
        assert "X-CV-Modal" not in view.request.headers
        assert view.request.session is case.source.request.session
        assert view.request.user is case.source.request.user
        assert view.object == case.blocker
        return True

    monkeypatch.setattr(target, "_cv_cancel_target_available", classmethod(available))
    if branch in {"denied", "disabled"}:
        # Restore policy composition without undoing fixture isolation.
        from crud_views.lib.view import CrudView

        monkeypatch.setattr(
            target, "_cv_cancel_target_available", classmethod(CrudView._cv_cancel_target_available.__func__)
        )
        hook = "cv_has_access" if branch == "denied" else "cv_action_enabled"
        monkeypatch.setattr(target, hook, classmethod(lambda *args: False))
        expected = False
    elif branch == "permission-denied":
        monkeypatch.setattr(target, "_cv_cancel_target_available", classmethod(fail(PermissionDenied())))
        expected = False
    elif branch in {"queryset-404", "queryset-error", "policy-404", "policy-error", "hook-404", "hook-reverse"}:
        error = NoReverseMatch if branch == "hook-reverse" else Http404 if branch.endswith("404") else RuntimeError
        hook = "get_queryset" if branch.startswith("queryset") else "_cv_cancel_target_available"
        if not branch.startswith("hook"):
            monkeypatch.setattr(target, hook, fail(error("application failure")))
    elif branch == "missing-row":
        monkeypatch.setattr(target, "get_queryset", lambda self: Contract.objects.none())
        expected = False
    elif branch == "queryset-get-404":
        from django.db.models import QuerySet

        class BrokenQuerySet(QuerySet):
            def get(self, *args, **kwargs):
                raise Http404("Application lookup failure")

        monkeypatch.setattr(target, "get_queryset", lambda self: BrokenQuerySet(model=Contract))
        error = Http404
    elif branch in {"cv-override", "permission-override", "method-override", "presentation", "queryset-init"}:
        kwargs = {
            "cv-override": {"cv_permission": "delete"},
            "permission-override": {"permission_required": "test1.change_contract"},
            "method-override": {"has_permission": lambda: True},
            "presentation": {"template_name": "custom.html"},
            "queryset-init": {"queryset": Contract.objects.none()},
        }[branch]
        case.route(target.as_view(**kwargs))
        candidate = f"/candidate/{case.blocker.pk}/"
        expected = branch == "presentation"
        if branch == "queryset-init":
            monkeypatch.setattr(target, "get_queryset", SingleObjectMixin.get_queryset)
        if branch == "permission-override":
            # Class policy permits this actor, but the real callback's instance
            # policy denies it. The preview must not advertise the candidate.
            assert target.cv_has_access(case.source.request.user, case.blocker)
            client = Client()
            client.force_login(case.source.request.user)
            assert client.get(candidate).status_code == 403
    elif branch in {"non-detail", "unregistered"}:

        def callback(request, **kwargs):
            return HttpResponse("other")

        if branch == "unregistered":

            class Other(target):
                pass

            callback = Other.as_view()
        case.route(callback)
        candidate = f"/candidate/{case.blocker.pk}/"
        expected = False
    elif branch == "wrong-row":
        other = Contract.objects.create(title="Other", publisher=case.source.object)
        candidate = case.url.replace(str(case.blocker.pk), str(other.pk))
        expected = False
    elif branch in {"lookup-kwarg", "slug", "pk-and-slug", "wrong-slug", "missing-coordinate", "unicode"}:
        kwargs = {"pk_url_kwarg": "row"}
        route = "lookup/<int:row>/"
        candidate = f"/lookup/{case.blocker.pk}/"
        if branch != "lookup-kwarg":
            kwargs = {"slug_url_kwarg": "label", "slug_field": "title"}
            route = "lookup/<str:label>/"
            case.blocker.title = "café" if branch == "unicode" else "slug"
            case.blocker.save()
            candidate = "/lookup/caf%C3%A9/" if branch == "unicode" else "/lookup/slug/"
        if branch in {"pk-and-slug", "wrong-slug"}:
            kwargs["query_pk_and_slug"] = True
            route = "lookup/<int:pk>/<str:label>/"
            candidate = f"/lookup/{case.blocker.pk}/{'wrong' if branch == 'wrong-slug' else 'slug'}/"
            expected = branch != "wrong-slug"
        if branch == "missing-coordinate":
            kwargs = {}
            error = AttributeError
        case.route(target.as_view(**kwargs), route)
    elif branch == "wrong-model":
        monkeypatch.setattr(target, "get_queryset", lambda self: Publisher.objects.all())
        candidate = case.url.replace(str(case.blocker.pk), str(case.source.object.pk))
        expected = False
    elif branch == "query-fragment":
        candidate += "?q=one&q=two#section"

    original = (
        case.source.request.path,
        case.source.request.GET.copy(),
        case.source.request.POST.copy(),
        case.source.request.META.copy(),
    )
    assert case.source.request.headers["X-CV-Modal"] == "true"  # cache headers before cloning
    monkeypatch.setattr(
        case.source, "cv_get_related_object_url", fail(error()) if branch.startswith("hook") else lambda obj: candidate
    )
    monkeypatch.setattr(target, "get_object", lambda *args: pytest.fail("Preview called overridden get_object"))
    adapter = getattr(case.source, "_cv_get_protected_object_url", case.source.cv_get_related_object_url)
    if error:
        with pytest.raises(error):
            adapter(case.blocker)
    else:
        assert adapter(case.blocker) == (candidate if expected else None)
    assert original == (
        case.source.request.path,
        case.source.request.GET,
        case.source.request.POST,
        case.source.request.META,
    )
    if expected and not error:
        assert len(calls) == 1
    if calls:
        assert len(calls) == 1
        if branch == "presentation":
            assert calls[0].template_name == "custom.html"
        if branch == "query-fragment":
            assert calls[0].request.GET.getlist("q") == ["one", "two"]


@pytest.mark.django_db
def test_protected_script_prefix(protected_destination, client_user_publisher_cascade_delete, monkeypatch, settings):
    from django.urls import get_script_prefix, set_script_prefix

    case = protected_destination
    old_prefix = get_script_prefix()
    settings.FORCE_SCRIPT_NAME = "/mounted"
    try:
        set_script_prefix("/mounted/")
        url = "/mounted" + case.url
        monkeypatch.setattr(case.source, "cv_get_related_object_url", lambda obj: url)
        seen = []

        def available(cls, user, obj, view):
            seen.append((view.request.path, view.request.path_info, view.request.META["SCRIPT_NAME"]))
            return True

        monkeypatch.setattr(case.target, "_cv_cancel_target_available", classmethod(available))
        adapter = getattr(case.source, "_cv_get_protected_object_url", case.source.cv_get_related_object_url)
        assert adapter(case.blocker) == url
        assert seen == [(url, case.url, "/mounted")]
        response = client_user_publisher_cascade_delete.get(url.removeprefix("/mounted"), SCRIPT_NAME="/mounted")
        assert response.status_code == 200
        assert response.wsgi_request.path == url
        assert response.content.decode() == f"contract:{case.blocker.pk}"
        monkeypatch.setattr(case.source, "cv_get_related_object_url", lambda obj: case.url)
        assert adapter(case.blocker) is None
    finally:
        set_script_prefix(old_prefix)


@pytest.mark.django_db
@pytest.mark.parametrize("preview", [False, True])
@pytest.mark.parametrize("link", [False, True])
@pytest.mark.parametrize("visible_count", [0, 1, 3])
@pytest.mark.parametrize("cascade", [False, True])
def test_protected_context_projection_matrix(protected_destination, monkeypatch, preview, link, visible_count, cascade):
    from crud_views.lib.deletion import DeleteInspection, RelatedObjects
    from tests.test1.app.models import Contract, Royalty

    case = protected_destination
    second = Contract.objects.create(title=case.blocker.title, publisher=case.source.object)
    # Distinct models can have the same typed PK. Equal labels and PKs must not
    # collapse the sequence supplied by inspection/filter providers.
    third = Royalty.objects.create(pk=case.blocker.pk, title=case.blocker.title, publisher=case.source.object)
    blockers = [third, second, case.blocker]
    tree = [case.source.object] if cascade else []
    summary = {"publisher": 1} if cascade else {}
    inspection = DeleteInspection(RelatedObjects(tree, summary, blockers), ())
    monkeypatch.setattr(case.source, "_cv_inspect_deletion", lambda: inspection)
    calls = []

    def filter_rows(user, related):
        assert related.protected == blockers
        assert all(hasattr(obj, "_meta") for obj in related.protected)
        return RelatedObjects(related.tree, related.summary, blockers[:visible_count])

    def url(obj):
        calls.append(obj)
        return case.url if obj is case.blocker else ""

    monkeypatch.setattr(case.source, "cv_filter_related_objects", filter_rows)
    monkeypatch.setattr(case.source, "cv_get_related_object_url", url)
    case.source.cv_show_related_objects = preview
    case.source.cv_link_related_objects = link
    context = case.source.get_context_data()
    assert context["has_protected_objects"] is True
    if not preview:
        assert not {"related_objects", "related_summary", "protected_objects"} & context.keys()
        assert calls == []
        return
    expected = [
        {"obj": obj, "url": case.url if link and obj is case.blocker else None} for obj in blockers[:visible_count]
    ]
    assert context["protected_objects"] == expected
    assert [entry["obj"] is obj for entry, obj in zip(context["protected_objects"], blockers, strict=False)] == [
        True
    ] * visible_count
    assert calls == (blockers[:visible_count] + tree if link else [])
    assert context["related_objects"] == ([{"obj": case.source.object, "url": None, "children": []}] if cascade else [])


@pytest.mark.django_db
@pytest.mark.parametrize("preview,link", [(False, False), (False, True), (True, False), (True, True)])
@pytest.mark.parametrize("modal", [False, True])
def test_protected_visibility_before_urls(
    protected_destination, monkeypatch, client_user_publisher_cascade_delete, preview, link, modal
):
    from django.contrib.auth.models import Permission

    case = protected_destination
    case.source.request.user.user_permissions.remove(Permission.objects.get(codename="view_contract"))
    source_class = type(case.source)
    monkeypatch.setattr(source_class, "cv_show_related_objects", preview)
    monkeypatch.setattr(source_class, "cv_link_related_objects", link)
    monkeypatch.setattr(source_class, "cv_modal", modal)
    seen = []
    monkeypatch.setattr(source_class, "cv_get_related_object_url", lambda self, obj: seen.append(obj))
    headers = {"HTTP_X_CV_MODAL": "true"} if modal else {}
    url = f"/publisher_cascade/{case.source.object.pk}/delete/"
    for method in ("get", "post"):
        response = getattr(client_user_publisher_cascade_delete, method)(url, {"confirm": "true"}, **headers)
        assert response.status_code == (422 if modal and method == "post" else 200)
        assert response.context["has_protected_objects"] is True
        if preview:
            assert response.context["protected_objects"] == []
        else:
            assert "protected_objects" not in response.context
        html = response.content.decode()
        assert "Visible blocker" not in html
        assert case.url not in html
        assert "<form" not in html
        assert "Other objects still reference this one" in html
    assert seen == []
    case.blocker.refresh_from_db()
    case.source.object.refresh_from_db()


@pytest.mark.parametrize("outer_autoescape", ["on", "off"])
@pytest.mark.parametrize("theme", ["stock", "body", "authorization-frame"])
def test_protected_body_escaping(outer_autoescape, theme):
    from django.template import Context, Template
    from django.utils.safestring import mark_safe
    from django.utils.translation import gettext, override
    from lxml import html as lxml_html

    from tests.test1.test_alerts import _theme_templates
    from tests.test1.test_authorization_templates import OVERRIDES

    body = "crud_views/snippets/delete/protected_objects.html"
    overrides = {}
    if theme == "body":
        overrides[body] = (
            "{% autoescape on %}<x-protected>{% for item in items %}{{ item.obj }}{% endfor %}"
            "</x-protected>{% endautoescape %}"
        )
    elif theme == "authorization-frame":
        overrides["crud_views/tags/alert.html"] = OVERRIDES["crud_views/tags/alert.html"]
    template = (
        "{% load crud_views i18n %}{% autoescape " + outer_autoescape + " %}"
        '{% cv_alert "error" heading=_("Deletion is blocked by protected relationships:") '
        'body_template="' + body + '" dismissible=True %}{% endautoescape %}'
    )
    items = [
        {"obj": '<script>alert("bad")</script>', "url": '/detail/?q=" onmouseover="bad&x=1'},
        {"obj": mark_safe("<b>Trusted label</b>"), "url": None},
        {"obj": "Plain text", "url": ""},
    ]
    with _theme_templates(overrides), override("de"):
        rendered = Template(template).render(Context({"items": items}))
        assert gettext("Deletion is blocked by protected relationships:") in rendered
    document = lxml_html.fromstring(rendered)
    assert document.get("role") == "alert"
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "<b>Trusted label</b>" in rendered
    assert "Plain text" in rendered
    if theme == "body":
        assert "<x-protected>" in rendered
    else:
        anchors = document.xpath(".//a")
        assert len(anchors) == 1
        assert anchors[0].attrib == {"href": items[0]["url"]}
    if theme != "authorization-frame":
        assert "alert-danger" in document.get("class")
        assert document.xpath(".//*[@data-cv-alert-dismiss]")
        assert document.xpath(".//strong")


@pytest.mark.django_db
def test_related_objects_not_shown_by_default(client_user_publisher_delete, cv_publisher, publisher_penguin):
    """Default DeleteView does not include related_objects in context."""
    from tests.test1.app.models import Book

    Book.objects.create(title="Book A", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_delete.get(f"/publisher/{pk}/delete/")
    assert response.status_code == 200
    assert "related_objects" not in response.context


@pytest.mark.django_db
def test_related_objects_shown_when_enabled(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """DeleteView with cv_show_related_objects=True includes related objects in context."""
    from tests.test1.app.models import Book

    Book.objects.create(title="Book A", publisher=publisher_penguin)
    Book.objects.create(title="Book B", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    assert "related_objects" in response.context
    assert "related_summary" in response.context
    summary = response.context["related_summary"]
    assert summary["book"] == 2


@pytest.mark.django_db
def test_related_objects_rendered_in_template(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """Related objects are rendered in the delete page HTML."""
    from django.contrib.auth.models import Permission

    from tests.test1.app.models import Book

    Book.objects.create(title="Hitchhiker's Guide", publisher=publisher_penguin)

    from django.contrib.auth.models import User

    user_obj = User.objects.get(username="user_publisher_cascade_delete")
    for codename in ("view_publisher", "view_book"):
        perm = Permission.objects.get(codename=codename)
        user_obj.user_permissions.add(perm)

    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    content = response.content.decode()
    assert "Hitchhiker" in content
    assert "book" in content.lower()


@pytest.mark.django_db
def test_delete_protection_shown_on_get(
    client_user_publisher_protected_delete, cv_publisher_protected, publisher_penguin
):
    """GET on a protected object shows errors instead of the delete form."""
    pk = publisher_penguin.pk
    response = client_user_publisher_protected_delete.get(f"/publisher_protected/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Cannot delete" in content
    assert "delete_protection_errors" in response.context
    assert "<form" not in content


@pytest.mark.django_db
def test_delete_protection_post_still_blocks(
    client_user_publisher_protected_delete, cv_publisher_protected, publisher_penguin
):
    """POST on a protected object still prevents deletion (defense in depth)."""
    pk = publisher_penguin.pk
    response = client_user_publisher_protected_delete.post(f"/publisher_protected/{pk}/delete/", {"confirm": True})
    assert response.status_code == 200
    from tests.test1.app.models import Publisher

    assert Publisher.objects.filter(pk=pk).exists()
    assert "Cannot delete" in response.content.decode()


@pytest.mark.django_db
def test_permission_filtering_hides_restricted_objects(cv_publisher_cascade, publisher_penguin):
    """User without view permission on Book sees counts, not individual objects."""
    from django.contrib.auth.models import User

    from tests.test1.app.models import Book

    Book.objects.create(title="Secret Book A", publisher=publisher_penguin)
    Book.objects.create(title="Secret Book B", publisher=publisher_penguin)

    user = User.objects.create_user(username="user_no_book_view", password="password")
    user_viewset_permission(user, cv_publisher_cascade, "delete")

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Secret Book A" not in content
    assert "Secret Book B" not in content
    assert "book" in content.lower()  # summary still shows model name


@pytest.mark.django_db
def test_permission_filtering_shows_permitted_objects(cv_publisher_cascade, publisher_penguin):
    """User with view permission on Book sees individual object details."""
    from django.contrib.auth.models import Permission, User

    from tests.test1.app.models import Book

    Book.objects.create(title="Visible Book", publisher=publisher_penguin)

    user = User.objects.create_user(username="user_with_book_view", password="password")
    user_viewset_permission(user, cv_publisher_cascade, "delete")
    perm = Permission.objects.get(codename="view_book")
    user.user_permissions.add(perm)

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Visible Book" in content


DANGER_ALERT = 'class="alert alert-danger" role="alert"'
BLOCKED_HEADING = "Deletion is blocked by protected relationships"
BLOCKED_LIST_HEADING = BLOCKED_HEADING + ":"
BLOCKED_SENTENCE = "Other objects still reference this one; remove or reassign them before deleting it."
MODAL_HEADERS = {"X-CV-Modal": "true"}


def _norm(html: str) -> str:
    return re.sub(r"\s+", " ", html)


def _context_instances(value, model, depth: int = 0) -> list:
    """Every ``model`` instance reachable through lists/tuples/sets/dicts of a context value."""
    if depth > 8:
        return []
    if isinstance(value, model):
        return [value]
    if isinstance(value, dict):
        return [hit for v in value.values() for hit in _context_instances(v, model, depth + 1)]
    if isinstance(value, (list, tuple, set)):
        return [hit for v in value for hit in _context_instances(v, model, depth + 1)]
    return []


def _response_instances(response, model) -> list:
    return [hit for layer in response.context for hit in _context_instances(layer.flatten(), model)]


@pytest.mark.django_db
def test_protected_objects_hidden_without_view_permission(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """D-07/D-08: a protected-only collection the user may not view keeps one blocked notice, no labels."""
    from tests.test1.app.models import Contract

    Contract.objects.create(title="Secret Contract", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    context = response.context
    assert context["related_summary"] == {}
    assert list(context["protected_objects"]) == []
    assert context["has_protected_objects"] is True
    assert _response_instances(response, Contract) == []
    content = _norm(response.content.decode())
    assert content.count(DANGER_ALERT) == 1
    assert BLOCKED_HEADING in content
    assert BLOCKED_SENTENCE in content
    assert BLOCKED_LIST_HEADING not in content
    assert "Secret Contract" not in content


@pytest.mark.django_db
def test_protected_objects_hidden_without_view_permission_modal(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin, monkeypatch
):
    """The modal partial carries the same independent notice when summary and labels are empty."""
    from tests.test1.app.models import Contract
    from tests.test1.app.views import PublisherCascadeDeleteView

    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_modal", True)
    Contract.objects.create(title="Secret Contract", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/", headers=MODAL_HEADERS)
    assert response.status_code == 200
    assert "crud_views/modal/content.html" in [t.name for t in response.templates]
    assert response.context["related_summary"] == {}
    assert list(response.context["protected_objects"]) == []
    assert response.context["has_protected_objects"] is True
    assert _response_instances(response, Contract) == []
    content = _norm(response.content.decode())
    assert content.count(DANGER_ALERT) == 1
    assert BLOCKED_HEADING in content
    assert BLOCKED_SENTENCE in content
    assert BLOCKED_LIST_HEADING not in content
    assert "Secret Contract" not in content


@pytest.mark.django_db
def test_protected_objects_shown_with_view_permission(
    client_user_publisher_cascade_delete, user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """A user granted view_contract sees the protected label inside the single blocked notice."""
    from django.contrib.auth.models import Permission

    from tests.test1.app.models import Contract

    contract = Contract.objects.create(title="Publishing Contract", publisher=publisher_penguin)
    user_publisher_cascade_delete.user_permissions.add(Permission.objects.get(codename="view_contract"))
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    assert response.context["protected_objects"] == [{"obj": contract, "url": None}]
    assert response.context["has_protected_objects"] is True
    content = _norm(response.content.decode())
    assert content.count(DANGER_ALERT) == 1
    assert BLOCKED_LIST_HEADING in content
    assert BLOCKED_SENTENCE not in content
    assert "<li>Publishing Contract</li>" in content


@pytest.mark.django_db
def test_no_protected_objects_no_notice(client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin):
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    assert response.context["has_protected_objects"] is False
    assert list(response.context["protected_objects"]) == []
    assert DANGER_ALERT not in _norm(response.content.decode())


@pytest.mark.django_db
@pytest.mark.parametrize("modal", [False, True])
def test_database_protect_post_returns_blocked_response_and_keeps_storage(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin, monkeypatch, modal
):
    from tests.test1.app.models import Contract, Publisher
    from tests.test1.app.views import PublisherCascadeDeleteView

    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_modal", True)
    calls = _spy_lifecycle(monkeypatch, PublisherCascadeDeleteView, ("cv_form_valid_hook", "cv_on_commit"))
    contract = Contract.objects.create(title="Secret Contract", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.post(
        f"/publisher_cascade/{pk}/delete/", {"confirm": True}, headers=MODAL_HEADERS if modal else {}
    )
    assert response.status_code == (422 if modal else 200)
    assert "<form" not in response.content.decode()
    assert BLOCKED_SENTENCE in response.content.decode()
    assert calls == []
    assert Publisher.objects.filter(pk=pk).exists()
    assert Contract.objects.filter(pk=contract.pk).exists()


@pytest.mark.django_db
def test_blocked_page_omits_confirmation_form(client_user_publisher_cascade_delete, publisher_penguin):
    from tests.test1.app.models import Contract

    Contract.objects.create(title="Secret Contract", publisher=publisher_penguin)
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{publisher_penguin.pk}/delete/")
    content = _norm(response.content.decode())
    assert content.count(DANGER_ALERT) == 1
    assert "<form" not in content
    assert "id_confirm" not in content
    assert 'name="delete"' not in content


@pytest.mark.django_db
@pytest.mark.parametrize("labelled", [False, True])
def test_blocked_notice_copy_hidden_and_labelled(
    client_user_publisher_cascade_delete, user_publisher_cascade_delete, publisher_penguin, labelled
):
    from django.contrib.auth.models import Permission

    from tests.test1.app.models import Contract

    Contract.objects.create(title="Publishing Contract", publisher=publisher_penguin)
    if labelled:
        user_publisher_cascade_delete.user_permissions.add(Permission.objects.get(codename="view_contract"))
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{publisher_penguin.pk}/delete/")
    content = _norm(response.content.decode())
    if labelled:
        assert BLOCKED_LIST_HEADING in content
        assert "<li>Publishing Contract</li>" in content
        assert BLOCKED_SENTENCE not in content
    else:
        assert BLOCKED_LIST_HEADING not in content
        assert content.count(BLOCKED_SENTENCE) == 1
        assert "Publishing Contract" not in content
    assert "<form" not in content


@pytest.mark.django_db
@pytest.mark.parametrize("blocked", [False, True])
def test_blocked_state_without_related_preview(client_user_publisher_delete, publisher_penguin, blocked):
    from tests.test1.app.models import Contract, Publisher

    if blocked:
        Contract.objects.create(title="Hidden", publisher=publisher_penguin)
    url = f"/publisher/{publisher_penguin.pk}/delete/"
    response = client_user_publisher_delete.get(url)
    assert response.context["has_protected_objects"] is blocked
    assert "protected_objects" not in response.context
    assert "related_summary" not in response.context
    assert ("<form" in response.content.decode()) is not blocked
    response = client_user_publisher_delete.post(url, {"confirm": True})
    assert response.status_code == (200 if blocked else 302)
    assert Publisher.objects.filter(pk=publisher_penguin.pk).exists() is blocked


@pytest.mark.django_db
def test_custom_protection_post_modal_422_keeps_storage(
    client_user_publisher_modal_protected_delete, cv_publisher_modal_protected, publisher_penguin
):
    """Custom cv_check_delete_protection errors re-render (422 in the modal), never write."""
    from tests.test1.app.models import Publisher

    pk = publisher_penguin.pk
    response = client_user_publisher_modal_protected_delete.post(
        f"/publisher_modal_protected/{pk}/delete/", {"confirm": True}, headers=MODAL_HEADERS
    )
    assert response.status_code == 422
    assert Publisher.objects.filter(pk=pk).exists()
    full = client_user_publisher_modal_protected_delete.post(
        f"/publisher_modal_protected/{pk}/delete/", {"confirm": True}
    )
    assert full.status_code == 200
    assert Publisher.objects.filter(pk=pk).exists()


# ── AUTH-01: HTTP DELETE is rejected (D-01/D-02) ─────────────────────────────


def _allow(response) -> set[str]:
    return {m.strip() for m in response.headers.get("Allow", "").split(",") if m.strip()}


def _spy_lifecycle(monkeypatch, view_class, names=("get_context_data", "cv_post_hook", "cv_form_valid_process")):
    calls = []
    for name in names:
        original = getattr(view_class, name)

        def spy(self, *args, _name=name, _original=original, **kwargs):
            calls.append(_name)
            return _original(self, *args, **kwargs)

        monkeypatch.setattr(view_class, name, spy)
    return calls


@pytest.mark.django_db
def test_http_delete_rejected_with_405(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin, monkeypatch
):
    from tests.test1.app.models import Publisher
    from tests.test1.app.views import PublisherCascadeDeleteView

    calls = _spy_lifecycle(monkeypatch, PublisherCascadeDeleteView)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.delete(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 405
    allow = _allow(response)
    assert "DELETE" not in allow
    assert {"GET", "POST", "OPTIONS"} <= allow
    assert calls == []
    assert Publisher.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_options_allow_omits_delete(client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin):
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.options(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    allow = _allow(response)
    assert "DELETE" not in allow
    assert {"GET", "POST", "OPTIONS"} <= allow


@pytest.mark.django_db
def test_http_delete_rejected_on_subclass_restoring_method_name(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin, monkeypatch
):
    """A subclass putting "delete" back into http_method_names is still stopped by the dispatch guard."""
    from django.views.generic import View

    from tests.test1.app.models import Publisher
    from tests.test1.app.views import PublisherCascadeDeleteView

    monkeypatch.setattr(PublisherCascadeDeleteView, "http_method_names", list(View.http_method_names))
    calls = _spy_lifecycle(monkeypatch, PublisherCascadeDeleteView)
    pk = publisher_penguin.pk
    url = f"/publisher_cascade/{pk}/delete/"
    response = client_user_publisher_cascade_delete.delete(url)
    assert response.status_code == 405
    assert "DELETE" not in _allow(response)
    options = client_user_publisher_cascade_delete.options(url)
    assert options.status_code == 200
    assert "DELETE" not in _allow(options)
    assert _allow(options) == _allow(response)
    assert calls == []
    assert Publisher.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_http_delete_rejection_keeps_modal_vary(client_user_author_modal, author_douglas_adams):
    from tests.test1.app.models import Author

    pk = author_douglas_adams.pk
    for headers in ({}, MODAL_HEADERS):
        response = client_user_author_modal.delete(f"/author_modal/{pk}/delete/", headers=headers)
        assert response.status_code == 405
        assert "X-CV-Modal" in response.headers.get("Vary", "")
    assert Author.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_http_delete_keeps_earlier_core_gates(client, cv_publisher_cascade, publisher_penguin):
    """Authentication and core permission gates still run before the method rejection."""
    from django.contrib.auth.models import User

    from tests.test1.app.models import Publisher

    pk = publisher_penguin.pk
    url = f"/publisher_cascade/{pk}/delete/"
    anonymous = client.delete(url)
    assert anonymous.status_code == 302
    assert "login" in anonymous.headers["Location"]

    user = User.objects.create_user(username="user_no_delete", password="password")
    client.force_login(user)
    assert client.delete(url).status_code == 403
    assert Publisher.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_http_delete_missing_target_core(client_user_publisher_cascade_delete, cv_publisher_cascade):
    """The core permission phase loads the object, so a missing target still 404s before the 405 guard."""
    assert client_user_publisher_cascade_delete.delete("/publisher_cascade/999999/delete/").status_code == 404


@pytest.mark.django_db
def test_delete_views_construct_without_custom_delete_warning(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """The guard leaves Django's delete() untouched, so Django 4.2 emits no DeleteViewCustomDeleteWarning."""
    import warnings

    from django.views.generic.edit import DeletionMixin

    from crud_views.lib.views import DeleteView, DeleteViewPermissionRequired
    from crud_views_guardian.lib.views import GuardianDeleteViewPermissionRequired
    from crud_views_polymorphic.lib import PolymorphicDeleteViewPermissionRequired
    from tests.test1.app.views import (
        AuthorModalDeleteView,
        GuardianPublisherCascadeDeleteView,
        PublisherCascadeDeleteView,
        VehicleDeleteView,
    )

    classes = [
        PublisherCascadeDeleteView,
        GuardianPublisherCascadeDeleteView,
        VehicleDeleteView,
        AuthorModalDeleteView,
    ]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        for view_class in classes:
            view_class()
        url = f"/publisher_cascade/{publisher_penguin.pk}/delete/"
        client_user_publisher_cascade_delete.get(url)
        client_user_publisher_cascade_delete.delete(url)
    assert [w for w in caught if w.category.__name__ == "DeleteViewCustomDeleteWarning"] == []
    for view_class in (
        DeleteView,
        DeleteViewPermissionRequired,
        GuardianDeleteViewPermissionRequired,
        PolymorphicDeleteViewPermissionRequired,
        *classes,
    ):
        assert view_class.delete is DeletionMixin.delete


@pytest.mark.django_db
def test_delete_protection_form_clean(publisher_penguin):
    """Form clean() raising ValidationError prevents deletion."""
    from django.contrib.auth.models import User

    from tests.test1.app.models import Publisher
    from tests.test1.app.views import cv_publisher_form_protected

    user = User.objects.create_user(username="user_form_clean_test", password="password")
    user_viewset_permission(user, cv_publisher_form_protected, "delete")

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.post(f"/publisher_form_protected/{pk}/delete/", {"confirm": True})
    assert response.status_code == 200
    assert Publisher.objects.filter(pk=pk).exists()
    assert "Form-level" in response.content.decode()


@pytest.mark.django_db
def test_successful_cascade_delete(client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin):
    """With cv_show_related_objects=True, POST still deletes object and cascaded relations."""
    from tests.test1.app.models import Book, Publisher

    book = Book.objects.create(title="Doomed Book", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.post(f"/publisher_cascade/{pk}/delete/", {"confirm": True})
    assert response.status_code == 302
    assert not Publisher.objects.filter(pk=pk).exists()
    assert not Book.objects.filter(pk=book.pk).exists()


@pytest.mark.django_db
def test_related_objects_linking(publisher_penguin):
    """With cv_link_related_objects=True, related objects with ViewSets are rendered as links."""
    from django.contrib.auth.models import Permission, User

    from tests.test1.app.models import Book
    from tests.test1.app.views import cv_publisher_linked

    Book.objects.create(title="Linked Book", publisher=publisher_penguin)

    user = User.objects.create_user(username="user_link_test", password="password")
    user_viewset_permission(user, cv_publisher_linked, "delete")
    # Grant view permissions so related objects are visible
    for codename in ("view_publisher", "view_book"):
        perm = Permission.objects.get(codename=codename)
        user.user_permissions.add(perm)

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_linked/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    # Related book should be rendered as a clickable link
    import re

    assert re.search(r"<a\s[^>]*>Linked Book</a>", content)


@pytest.mark.django_db
def test_related_objects_linking_context_has_dict_tree(publisher_penguin):
    """With cv_link_related_objects=True, context['related_objects'] is a list of dicts with url keys."""
    from django.contrib.auth.models import Permission, User

    from tests.test1.app.models import Book
    from tests.test1.app.views import cv_publisher_linked

    Book.objects.create(title="Context Book", publisher=publisher_penguin)

    user = User.objects.create_user(username="user_link_ctx_test", password="password")
    user_viewset_permission(user, cv_publisher_linked, "delete")
    for codename in ("view_publisher", "view_book"):
        perm = Permission.objects.get(codename=codename)
        user.user_permissions.add(perm)

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_linked/{pk}/delete/")
    assert response.status_code == 200

    related_objects = response.context["related_objects"]
    assert isinstance(related_objects, list)
    assert len(related_objects) > 0
    # Each node should be a dict with obj, url, children keys
    node = related_objects[0]
    assert "obj" in node
    assert "url" in node
    assert "children" in node


@pytest.mark.django_db
def test_related_objects_no_linking_when_disabled(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """With cv_link_related_objects=False (default), related objects are NOT rendered as links."""
    from django.contrib.auth.models import Permission, User

    from tests.test1.app.models import Book

    Book.objects.create(title="Unlinked Book", publisher=publisher_penguin)

    # Grant view permissions so objects are visible in the tree
    user_obj = User.objects.get(username="user_publisher_cascade_delete")
    for codename in ("view_publisher", "view_book"):
        perm = Permission.objects.get(codename=codename)
        user_obj.user_permissions.add(perm)

    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Unlinked Book" in content
    # The related object text should NOT appear inside an <a> tag
    import re

    assert not re.search(r"<a\s[^>]*>Unlinked Book</a>", content)


def _grant_view_publisher_and_book():
    from django.contrib.auth.models import Permission, User

    user_obj = User.objects.get(username="user_publisher_cascade_delete")
    for codename in ("view_publisher", "view_book"):
        user_obj.user_permissions.add(Permission.objects.get(codename=codename))


@pytest.mark.django_db
def test_related_summary_items_are_ready_strings(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    from tests.test1.app.models import Book

    Book.objects.create(title="Book A", publisher=publisher_penguin)
    Book.objects.create(title="Book B", publisher=publisher_penguin)
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{publisher_penguin.pk}/delete/")
    assert response.context["related_summary_items"] == ["book: 2"]


@pytest.mark.django_db
def test_delete_alerts_render_through_the_frame(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """#250: the protected, summary and tree alerts all come out of tags/alert.html."""
    from tests.test1.app.models import Book, Contract

    _grant_view_publisher_and_book()
    Book.objects.create(title="Book A", publisher=publisher_penguin)
    Contract.objects.create(title="Publishing Contract", publisher=publisher_penguin)
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{publisher_penguin.pk}/delete/")
    content = re.sub(r"\s+", " ", response.content.decode())
    assert content.count('class="alert alert-danger" role="alert"') == 1
    assert content.count('class="alert alert-warning" role="alert"') == 2
    assert "<li>book: 1</li>" in content
    assert "Book A" in content


def test_delete_alert_headings_translate():
    from django.template.loader import render_to_string
    from django.utils import translation

    with translation.override("de"):
        html = render_to_string(
            "crud_views/snippets/delete/protection_errors.html", {"delete_protection_errors": ["x"]}
        )
    assert "Dieses Objekt kann nicht gelöscht werden:" in html
    assert 'role="alert"' in html


@pytest.mark.django_db
@pytest.mark.parametrize("labelled", [False, True])
def test_blocked_notice_renders_in_german(
    client_user_publisher_cascade_delete, user_publisher_cascade_delete, publisher_penguin, labelled
):
    from django.contrib.auth.models import Permission
    from django.utils import translation

    from tests.test1.app.models import Contract

    Contract.objects.create(title="Publishing Contract", publisher=publisher_penguin)
    if labelled:
        user_publisher_cascade_delete.user_permissions.add(Permission.objects.get(codename="view_contract"))
    with translation.override("de"):
        response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{publisher_penguin.pk}/delete/")
    content = _norm(response.content.decode())
    heading = "Das Löschen wird durch geschützte Beziehungen verhindert"
    sentence = (
        "Andere Objekte verweisen noch auf dieses Objekt; entfernen Sie diese Verweise oder ordnen Sie sie neu zu, "
        "bevor Sie es löschen."
    )
    assert "<form" not in content
    if labelled:
        assert f"<strong>{heading}:</strong>" in content
        assert "<li>Publishing Contract</li>" in content
        assert sentence not in content
    else:
        assert f"<strong>{heading}</strong>" in content
        assert sentence in content
        assert "Publishing Contract" not in content
    assert BLOCKED_HEADING not in content
    assert BLOCKED_SENTENCE not in content


def _assert_guard_in_mro(view_class):
    from django.views import generic

    from crud_views.lib.view import CrudView
    from crud_views.lib.views.delete import _DeleteMethodGuardMixin

    mro = view_class.__mro__
    assert mro.index(CrudView) < mro.index(_DeleteMethodGuardMixin) < mro.index(generic.DeleteView)


def _spy_raw_delete_handler(monkeypatch) -> list:
    """Spy on Django's DeletionMixin.delete itself, so concrete classes keep ``delete is DeletionMixin.delete``."""
    from django.views.generic.edit import DeletionMixin

    entered = []
    original = DeletionMixin.delete

    def spy(self, request, *args, **kwargs):
        entered.append(request.method)
        return original(self, request, *args, **kwargs)

    monkeypatch.setattr(DeletionMixin, "delete", spy)
    return entered


@pytest.mark.django_db
def test_registered_core_class_restoring_delete_stays_guarded(
    client_user_publisher_delete, cv_publisher, publisher_penguin, monkeypatch
):
    """A18/A22: the registered PublisherDeleteView, patched to list "delete" again, inherits the dispatch guard."""
    from django.views.generic import View

    from crud_views.lib.views import DeleteView
    from tests.test1.app.models import Publisher
    from tests.test1.app.views import PublisherDeleteView

    _assert_guard_in_mro(PublisherDeleteView)
    original = PublisherDeleteView.http_method_names
    inherited = list(DeleteView.http_method_names)
    url = f"/publisher/{publisher_penguin.pk}/delete/"
    with monkeypatch.context() as patch:
        patch.setattr(PublisherDeleteView, "http_method_names", [*View.http_method_names])
        assert "delete" in PublisherDeleteView.http_method_names
        entered = _spy_raw_delete_handler(patch)
        response = client_user_publisher_delete.delete(url)
        options = client_user_publisher_delete.options(url)
        assert response.status_code == 405
        assert options.status_code == 200
        assert "DELETE" not in _allow(response)
        assert _allow(options) == _allow(response)
        assert entered == []
    assert PublisherDeleteView.http_method_names is original
    assert "delete" not in PublisherDeleteView.http_method_names
    assert DeleteView.http_method_names == inherited
    assert Publisher.objects.filter(pk=publisher_penguin.pk).exists()


@pytest.mark.django_db
def test_database_restrict_preview_and_post_keep_storage(client_user_publisher_cascade_delete, publisher_penguin):
    from tests.test1.app.models import Publisher, Royalty

    royalty = Royalty.objects.create(publisher=publisher_penguin, title="Hidden Royalty")
    url = f"/publisher_cascade/{publisher_penguin.pk}/delete/"
    response = client_user_publisher_cascade_delete.get(url)
    assert response.context["has_protected_objects"] is True
    assert response.context["protected_objects"] == []
    assert _response_instances(response, Royalty) == []
    assert "<form" not in response.content.decode()
    response = client_user_publisher_cascade_delete.post(url, {"confirm": True})
    assert response.status_code == 200
    assert BLOCKED_SENTENCE in response.content.decode()
    assert "<form" not in response.content.decode()
    assert Publisher.objects.filter(pk=publisher_penguin.pk).exists()
    assert Royalty.objects.filter(pk=royalty.pk).exists()


def _delete_probe(monkeypatch, atomic):
    """Exercise the registered route with real inspection, writes and commit callbacks."""
    from tests.test1.app.views import PublisherDeleteView

    calls = []
    monkeypatch.setattr(PublisherDeleteView, "cv_atomic", atomic)
    monkeypatch.setattr(PublisherDeleteView, "cv_form_valid_hook", lambda self, context: calls.append("success"))
    monkeypatch.setattr(PublisherDeleteView, "cv_on_commit", lambda self, context: calls.append("commit"))
    original = PublisherDeleteView._cv_protection_response

    def response(self, context):
        calls.append("blocked")
        return original(self, context)

    monkeypatch.setattr(PublisherDeleteView, "_cv_protection_response", response)
    return PublisherDeleteView, calls


def _protector(error_name, publisher):
    from tests.test1.app.models import Contract, Royalty

    model = Contract if error_name == "ProtectedError" else Royalty
    return model.objects.create(publisher=publisher, title="Hidden protector")


def _error_type(error_name):
    from django.db.models import ProtectedError, RestrictedError

    return ProtectedError if error_name == "ProtectedError" else RestrictedError


@pytest.mark.django_db
@pytest.mark.parametrize("preview", [False, True])
@pytest.mark.parametrize("method", ["get", "post"])
def test_delete_safe_preview_provider_called_once(
    client_user_publisher_delete, publisher_penguin, monkeypatch, preview, method
):
    from tests.test1.app.models import Contract
    from tests.test1.app.views import PublisherDeleteView

    contract = Contract.objects.create(title="Never projected", publisher=publisher_penguin)
    seen = []

    def describe(self, boundaries, *, using):
        seen.append((self.object.pk, using, boundaries))
        return ()

    monkeypatch.setattr(PublisherDeleteView, "cv_get_delete_preview", describe)
    monkeypatch.setattr(PublisherDeleteView, "cv_show_related_objects", preview)
    response = getattr(client_user_publisher_delete, method)(
        f"/publisher/{publisher_penguin.pk}/delete/", {"confirm": True}
    )
    assert seen == [(publisher_penguin.pk, "default", ())]
    assert contract.pk is not None
    assert response.context["has_protected_objects"] is True
    assert _response_instances(response, Contract) == []
    assert ("protected_objects" in response.context) is preview


@pytest.mark.django_db
def test_delete_default_collection_uses_write_router(client_user_publisher_delete, publisher_penguin, monkeypatch):
    from crud_views.lib.views import delete

    seen = []
    original = delete.inspect_deletion

    def inspect(target, *, using):
        seen.append((target.pk, using))
        return original(target, using=using)

    routed = []

    def db_for_write(model, **hints):
        routed.append((model, hints))
        return "default"

    monkeypatch.setattr(delete.router, "db_for_write", db_for_write)
    monkeypatch.setattr(delete, "inspect_deletion", inspect)
    response = client_user_publisher_delete.get(f"/publisher/{publisher_penguin.pk}/delete/")
    assert response.context["has_protected_objects"] is False
    assert seen == [(publisher_penguin.pk, "default")]
    assert routed == [(type(publisher_penguin), {"instance": publisher_penguin})]


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["get", "post"])
def test_delete_legacy_preview_override_rejected_without_invocation(
    client_user_publisher_delete, publisher_penguin, monkeypatch, method
):
    from django.core.exceptions import ImproperlyConfigured

    from tests.test1.app.views import PublisherDeleteView

    calls = []
    monkeypatch.setattr(PublisherDeleteView, "cv_get_related_objects", lambda self: calls.append("unsafe"))
    with pytest.raises(ImproperlyConfigured, match="cv_get_delete_preview"):
        getattr(client_user_publisher_delete, method)(f"/publisher/{publisher_penguin.pk}/delete/", {"confirm": True})
    assert calls == []


@pytest.mark.django_db
@pytest.mark.parametrize("modal", [False, True])
def test_blocked_invalid_confirmation_keeps_invalid_path(
    client_user_publisher_delete, publisher_penguin, monkeypatch, modal
):
    from tests.test1.app.models import Publisher
    from tests.test1.app.views import PublisherDeleteView

    protector = _protector("ProtectedError", publisher_penguin)
    monkeypatch.setattr(PublisherDeleteView, "cv_modal", True)
    calls = _spy_lifecycle(
        monkeypatch, PublisherDeleteView, ("cv_form_invalid_hook", "cv_form_valid_hook", "cv_on_commit")
    )
    response = client_user_publisher_delete.post(
        f"/publisher/{publisher_penguin.pk}/delete/", {}, headers=MODAL_HEADERS if modal else {}
    )
    assert response.status_code == (422 if modal else 200)
    assert response.context["form"].errors
    assert "<form" not in response.content.decode()
    assert calls == ["cv_form_invalid_hook"]
    assert Publisher.objects.filter(pk=publisher_penguin.pk).exists()
    assert type(protector).objects.filter(pk=protector.pk).exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
@pytest.mark.parametrize("nested", [False, True])
def test_delete_callback_protection_error_propagates_after_real_commit(
    client_user_publisher_delete, monkeypatch, atomic, error_name, nested
):
    from django.db import connection

    from tests.test1.app.models import Publisher

    view, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    unrelated = Publisher.objects.create(name="Unrelated")
    protector = _protector(error_name, unrelated)
    error = _error_type(error_name)("Callback failure", {protector})
    raised = []

    def callback(self, context):
        calls.append("commit")
        assert not connection.in_atomic_block
        try:
            if nested:
                unrelated.delete()
            raise error
        except _error_type(error_name) as exc:
            raised.append(exc)
            raise

    monkeypatch.setattr(view, "cv_on_commit", callback)
    with pytest.raises(_error_type(error_name)) as caught:
        client_user_publisher_delete.post(f"/publisher/{target.pk}/delete/", {"confirm": True})
    assert caught.value is raised[0]
    assert not Publisher.objects.filter(pk=target.pk).exists()
    assert Publisher.objects.filter(pk=unrelated.pk).exists()
    assert calls == ["success", "commit"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
def test_delete_success_hook_protection_error_keeps_atomic_semantics(
    client_user_publisher_delete, monkeypatch, atomic, error_name
):
    from tests.test1.app.models import Publisher

    view, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    error = _error_type(error_name)("Success hook failure", set())

    def success(self, context):
        calls.append("success")
        raise error

    monkeypatch.setattr(view, "cv_form_valid_hook", success)
    with pytest.raises(_error_type(error_name)) as caught:
        client_user_publisher_delete.post(f"/publisher/{target.pk}/delete/", {"confirm": True})
    assert caught.value is error
    assert Publisher.objects.filter(pk=target.pk).exists() is atomic
    assert calls == ["success"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
@pytest.mark.parametrize("stage", ["before", "after", "write_then_protected"])
def test_delete_model_override_protection_error_propagates(
    client_user_publisher_delete, monkeypatch, atomic, error_name, stage
):
    from django.db.models import Model

    from tests.test1.app.models import Publisher

    _, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    if stage == "write_then_protected":
        from tests.test1.app.views import PublisherDeleteView

        monkeypatch.setattr(PublisherDeleteView, "cv_post_hook", lambda self, context: _protector(error_name, target))
    error = _error_type(error_name)("Model override failure", set())
    raised = []

    def delete(self, *args, **kwargs):
        try:
            if stage == "before":
                raise error
            Publisher.objects.create(name="Side effect")
            Model.delete(self, *args, **kwargs)
            raise error
        except _error_type(error_name) as exc:
            raised.append(exc)
            raise

    monkeypatch.setattr(Publisher, "delete", delete)
    with pytest.raises(_error_type(error_name)) as caught:
        client_user_publisher_delete.post(f"/publisher/{target.pk}/delete/", {"confirm": True})
    assert caught.value is raised[0]
    assert Publisher.objects.filter(pk=target.pk).exists() is (stage != "after" or atomic)
    assert Publisher.objects.filter(name="Side effect").exists() is (stage != "before" and not atomic)
    assert calls == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
@pytest.mark.parametrize("signal_name", ["pre_delete", "post_delete"])
def test_delete_signal_protection_error_propagates(
    client_user_publisher_delete, monkeypatch, atomic, error_name, signal_name
):
    from django.db.models import signals

    from tests.test1.app.models import Publisher

    _, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    error = _error_type(error_name)("Signal failure", set())

    def receiver(**kwargs):
        calls.append(signal_name)
        raise error

    signal = getattr(signals, signal_name)
    signal.connect(receiver, sender=Publisher, weak=False)
    try:
        with pytest.raises(_error_type(error_name)) as caught:
            client_user_publisher_delete.post(f"/publisher/{target.pk}/delete/", {"confirm": True})
        assert caught.value is error
        assert Publisher.objects.filter(pk=target.pk).exists()
        assert calls == [signal_name]
    finally:
        signal.disconnect(receiver, sender=Publisher)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
def test_delete_signal_commit_protection_error_propagates(
    client_user_publisher_delete, monkeypatch, atomic, error_name
):
    from django.db import connection, transaction
    from django.db.models.signals import post_delete

    from tests.test1.app.models import Publisher

    _, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    error = _error_type(error_name)("Signal callback failure", set())

    def callback():
        calls.append("signal_commit")
        assert not connection.in_atomic_block
        raise error

    def receiver(**kwargs):
        transaction.on_commit(callback)

    post_delete.connect(receiver, sender=Publisher, weak=False)
    try:
        with pytest.raises(_error_type(error_name)) as caught:
            client_user_publisher_delete.post(f"/publisher/{target.pk}/delete/", {"confirm": True})
        assert caught.value is error
        assert not Publisher.objects.filter(pk=target.pk).exists()
        assert calls == (["success", "signal_commit"] if atomic else ["signal_commit"])
    finally:
        post_delete.disconnect(receiver, sender=Publisher)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("modal", [False, True])
def test_delete_success_real_commit_order(client_user_publisher_delete, monkeypatch, atomic, modal):
    from django.db import connection
    from django.db.models import Model

    from tests.test1.app.models import Publisher

    view, calls = _delete_probe(monkeypatch, atomic)
    monkeypatch.setattr(view, "cv_modal", True)
    target = Publisher.objects.create(name="Target")

    def delete(self, *, using):
        calls.append("delete")
        assert using == "default"
        return Model.delete(self, using=using)

    def callback(self, context):
        assert not connection.in_atomic_block
        calls.append("commit")

    monkeypatch.setattr(Publisher, "delete", delete)
    monkeypatch.setattr(view, "cv_on_commit", callback)
    response = client_user_publisher_delete.post(
        f"/publisher/{target.pk}/delete/", {"confirm": True}, headers=MODAL_HEADERS if modal else {}
    )
    assert response.status_code == (204 if modal else 302)
    if modal:
        assert response.headers["X-CV-Redirect"]
    assert calls == ["delete", "success", "commit"]
    assert not Publisher.objects.filter(pk=target.pk).exists()


def _collection_snapshot():
    from tests.test1.app.models import Book, BookNote, Contract, Publisher, Royalty

    return {
        model: list(
            model.objects.exclude(**({"name": "Side effect"} if model is Publisher else {})).order_by("pk").values()
        )
        for model in (Publisher, Book, BookNote, Contract, Royalty)
    }


def _assert_collection_extension_propagates(client, target, calls, atomic, error_name, before):
    from tests.test1.app.models import Publisher

    with pytest.raises(_error_type(error_name)) as caught:
        client.post(f"/publisher/{target.pk}/delete/", {"confirm": True})
    assert _collection_snapshot() == before
    assert Publisher.objects.filter(name="Side effect").exists() is not atomic
    assert "success" not in calls
    assert "commit" not in calls
    assert "blocked" not in calls
    return caught.value


def _assert_handler_error(error, original, error_name, objects):
    assert error is original  # The package adapter never aggregates custom errors.
    records = error.protected_objects if error_name == "ProtectedError" else error.restricted_objects
    assert set(objects) <= set(records)


def _stage_native_blocker(monkeypatch, view, target, error_name, snapshot):
    """Introduce a real race after real preview; include that deliberate write in the row baseline."""

    def post(self, context):
        assert context["has_protected_objects"] is False
        _protector(error_name, target)
        snapshot.update(_collection_snapshot())

    monkeypatch.setattr(view, "cv_post_hook", post)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
@pytest.mark.parametrize("mode", ["raise", "nested_delete", "return"])
def test_delete_custom_relationship_handler_propagates_after_real_commit(
    client_user_publisher_delete, monkeypatch, atomic, error_name, mode
):
    from tests.test1.app.models import Book, Publisher

    view, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    book = Book.objects.create(title="Cascade", publisher=target)
    unrelated = Publisher.objects.create(name="Unrelated")
    protector = _protector(error_name, unrelated)
    raised = []

    def handler(collector, field, objects, using):
        calls.append("handler")
        Publisher.objects.create(name="Side effect")
        # Changing the handler back now must not retroactively certify the collection.
        if mode == "return":
            from django.db.models import CASCADE

            monkeypatch.setattr(field.remote_field, "on_delete", CASCADE)
            return
        try:
            if mode == "nested_delete":
                unrelated.delete()
            raise _error_type(error_name)("Custom handler", {book})
        except _error_type(error_name) as error:
            raised.append(error)
            raise

    monkeypatch.setattr(Book._meta.get_field("publisher").remote_field, "on_delete", handler)
    before = _collection_snapshot()
    if mode == "return":
        _stage_native_blocker(monkeypatch, view, target, error_name, before)
    error = _assert_collection_extension_propagates(
        client_user_publisher_delete, target, calls, atomic, error_name, before
    )
    assert calls == ["handler"]
    if mode != "return":
        _assert_handler_error(error, raised[0], error_name, [protector if mode == "nested_delete" else book])


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
def test_delete_nested_relationship_handler_propagates_after_real_commit(
    client_user_publisher_delete, monkeypatch, atomic, error_name
):
    from tests.test1.app.models import Book, BookNote, Publisher

    _, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    book = Book.objects.create(title="Cascade", publisher=target)
    note = BookNote.objects.create(book=book, note="Nested")
    original = _error_type(error_name)("Nested handler", {note})

    def handler(collector, field, objects, using):
        calls.append("nested_handler")
        Publisher.objects.create(name="Side effect")
        raise original

    monkeypatch.setattr(BookNote._meta.get_field("book").remote_field, "on_delete", handler)
    before = _collection_snapshot()
    error = _assert_collection_extension_propagates(
        client_user_publisher_delete, target, calls, atomic, error_name, before
    )
    assert calls == ["nested_handler"]
    _assert_handler_error(error, original, error_name, [note])


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
@pytest.mark.parametrize("configured", ["SET", "SET_DEFAULT"])
def test_delete_callable_relationship_default_propagates_after_real_commit(
    client_user_publisher_delete, monkeypatch, atomic, error_name, configured
):
    from django.db.models import SET, SET_DEFAULT

    from tests.test1.app.models import Book, Publisher

    view, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    Book.objects.create(title="Cascade", publisher=target)

    def default():
        calls.append("default")
        return Publisher.objects.create(name="Side effect").pk

    field = Book._meta.get_field("publisher")
    if configured == "SET":
        monkeypatch.setattr(field.remote_field, "on_delete", SET(default))
    else:
        monkeypatch.setattr(field.remote_field, "on_delete", SET_DEFAULT)
        # Materialize the original cached default before replacing it, so teardown restores it too.
        original_default = field._get_default
        monkeypatch.setattr(field, "default", default)
        monkeypatch.setattr(field, "_get_default", default)
        assert original_default is not default
    assert calls == []
    before = _collection_snapshot()
    _stage_native_blocker(monkeypatch, view, target, error_name, before)
    _assert_collection_extension_propagates(client_user_publisher_delete, target, calls, atomic, error_name, before)
    assert calls == ["default"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
def test_delete_collection_loader_error_propagates_unchanged(
    client_user_publisher_delete, monkeypatch, atomic, error_name
):

    from tests.test1.app.models import Book, Publisher

    view, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    Book.objects.create(title="Cascade", publisher=target)
    error = _error_type(error_name)("Loader error", set())
    original_from_db = Book.from_db.__func__

    def from_db(cls, db, field_names, values):
        # Django 4.2's exception reporter can repr/evaluate local querysets after
        # atomic unwind. Keep the controlled failing read scoped to collection.
        monkeypatch.setattr(Book, "from_db", classmethod(original_from_db))
        calls.append("loader")
        Publisher.objects.create(name="Side effect")
        raise error

    assert calls == []
    before = _collection_snapshot()

    def post(self, context):
        assert context["has_protected_objects"] is False
        monkeypatch.setattr(Book, "from_db", classmethod(from_db))

    monkeypatch.setattr(view, "cv_post_hook", post)
    caught = _assert_collection_extension_propagates(
        client_user_publisher_delete, target, calls, atomic, error_name, before
    )
    assert caught is error
    assert calls == ["loader"]


@pytest.mark.parametrize(
    "handler_name,eligible",
    [
        ("CASCADE", True),
        ("PROTECT", True),
        ("RESTRICT", True),
        ("SET_NULL", True),
        ("DO_NOTHING", True),
        ("custom", False),
        ("SET-value", False),
        ("SET-callable", False),
        ("SET_DEFAULT", False),
    ],
)
@pytest.mark.django_db
def test_delete_empty_relationship_inspection_completeness(publisher_penguin, monkeypatch, handler_name, eligible):
    from django.db import models

    from crud_views.lib.deletion import inspect_deletion
    from tests.test1.app.models import Book

    def unknown(*args):
        pytest.fail("Metadata classifier executed a callback")

    if handler_name == "custom":
        handler = unknown
    elif handler_name.startswith("SET-"):
        handler = models.SET(unknown if handler_name == "SET-callable" else 1)
    else:
        handler = getattr(models, handler_name)
    monkeypatch.setattr(Book._meta.get_field("publisher").remote_field, "on_delete", handler)
    inspection = inspect_deletion(publisher_penguin, using="default")
    assert inspection.complete is eligible
    assert inspection.related.tree == [publisher_penguin]
    assert inspection.related.protected == []


@pytest.mark.django_db
@pytest.mark.parametrize("extension", ["manager", "queryset", "init", "from_db", "pre_init", "post_init"])
@pytest.mark.parametrize("method", ["get", "post"])
def test_delete_preview_read_errors_propagate(
    client_user_publisher_delete, publisher_penguin, monkeypatch, extension, method
):
    from django.db import models
    from django.db.models import signals

    from tests.test1.app.models import Book

    Book.objects.create(title="Read failure", publisher=publisher_penguin)
    error = RuntimeError("Unexpected ORM read failure")

    def fail(*args, **kwargs):
        raise error

    if extension == "manager":

        class CustomManager(models.Manager):
            def get_queryset(self):
                raise error

        monkeypatch.setitem(Book._meta.__dict__, "base_manager", CustomManager())
    elif extension == "queryset":

        class CustomQuerySet(models.QuerySet):
            def __iter__(self):
                raise error

        monkeypatch.setattr(Book._base_manager, "_queryset_class", CustomQuerySet)
    elif extension == "init":
        monkeypatch.setattr(Book, "__init__", fail)
    elif extension == "from_db":
        monkeypatch.setattr(Book, "from_db", classmethod(fail))
    else:
        signal = getattr(signals, extension)

        signal.connect(fail, sender=Book, weak=False)
    try:
        with pytest.raises(RuntimeError) as caught:
            getattr(client_user_publisher_delete, method)(
                f"/publisher/{publisher_penguin.pk}/delete/", {"confirm": True}
            )
        assert caught.value is error
    finally:
        if extension in ("pre_init", "post_init"):
            signal.disconnect(fail, sender=Book)


@pytest.mark.django_db
def test_delete_private_and_unknown_field_boundaries(publisher_penguin, monkeypatch):
    from types import SimpleNamespace

    from crud_views.lib import deletion
    from tests.test1.app.models import Book, Publisher

    events = []
    private = SimpleNamespace(
        name="private", model=Publisher, bulk_related_objects=lambda *args: events.append("private")
    )
    monkeypatch.setattr(Publisher._meta, "private_fields", [private])
    monkeypatch.setattr(
        deletion,
        "get_candidate_relations_to_delete",
        lambda opts: [SimpleNamespace(field=SimpleNamespace(name="unknown", model=Book))],
    )
    inspection = deletion.inspect_deletion(publisher_penguin, using="default")
    assert not inspection.complete
    assert {(boundary.kind, boundary.field_name) for boundary in inspection.boundaries} == {
        ("private_relation", "private"),
        ("on_delete", "unknown"),
    }
    assert {(boundary.kind, boundary.field_model) for boundary in inspection.boundaries} == {
        ("private_relation", Publisher),
        ("on_delete", Book),
    }
    assert events == []


@pytest.mark.django_db
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
def test_delete_target_collection_provenance(publisher_penguin, error_name):
    from crud_views.lib.deletion import _NativeDeleteBlocked, execute_deletion

    _protector(error_name, publisher_penguin)
    with pytest.raises(_NativeDeleteBlocked) as caught:
        execute_deletion(publisher_penguin, using="default")
    assert isinstance(caught.value.__cause__, _error_type(error_name))


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
@pytest.mark.parametrize("modal", [False, True])
def test_delete_native_target_backstop_keeps_storage(
    client_user_publisher_cascade_delete, monkeypatch, atomic, error_name, modal
):
    from tests.test1.app.models import Publisher
    from tests.test1.app.views import PublisherCascadeDeleteView

    target = Publisher.objects.create(name="Native target")
    view = PublisherCascadeDeleteView
    monkeypatch.setattr(view, "cv_atomic", atomic)
    monkeypatch.setattr(view, "cv_modal", True)
    preview_calls = []

    original = view._cv_inspect_deletion

    def inspect(self):
        preview_calls.append(self.object.pk)
        result = original(self)
        assert result.related.tree == [self.object]
        assert result.related.protected == []
        return result

    monkeypatch.setattr(view, "_cv_inspect_deletion", inspect)
    calls = _spy_lifecycle(monkeypatch, view, ("cv_form_valid_hook", "cv_on_commit"))
    before = _collection_snapshot()
    _stage_native_blocker(monkeypatch, view, target, error_name, before)
    response = client_user_publisher_cascade_delete.post(
        f"/publisher_cascade/{target.pk}/delete/", {"confirm": True}, headers=MODAL_HEADERS if modal else {}
    )
    assert response.status_code == (422 if modal else 200)
    assert response.context["has_protected_objects"] is True
    content = _norm(response.content.decode())
    assert content.count(f"<strong>{BLOCKED_HEADING}</strong>") == 1
    assert content.count(BLOCKED_SENTENCE) == 1
    assert BLOCKED_LIST_HEADING not in content
    assert "<form" not in content
    from tests.test1.app.models import Contract, Royalty

    assert "Hidden protector" not in content
    assert _response_instances(response, Contract if error_name == "ProtectedError" else Royalty) == []
    assert preview_calls == [target.pk]
    assert _collection_snapshot() == before
    assert calls == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
def test_delete_unknown_collector_type_propagates(client_user_publisher_delete, monkeypatch, atomic, error_name):
    from crud_views.lib import deletion
    from tests.test1.app.models import Publisher

    _, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    raised = []

    error = _error_type(error_name)("Custom collector failure", set())

    class UnknownCollector(deletion._DeleteCollector):
        def collect(self, *args, **kwargs):
            raised.append(error)
            raise error

    monkeypatch.setattr(deletion, "_DeleteCollector", UnknownCollector)
    before = _collection_snapshot()
    with pytest.raises(_error_type(error_name)) as caught:
        client_user_publisher_delete.post(f"/publisher/{target.pk}/delete/", {"confirm": True})
    assert caught.value is raised[-1]
    assert _collection_snapshot() == before
    assert calls == []
