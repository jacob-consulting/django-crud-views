"""URI input follows the same decoding boundary as a real Django request."""

from urllib.parse import quote

import pytest
from django.http import HttpResponse
from django.test import override_settings
from django.urls import path, reverse

from crud_views.lib.access_trace import trace_access
from crud_views.lib.views import DetailView, ListView
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Publisher
from tests.test1.test_ancestor_authorization import _user, isolated_routes
from tests.test1.test_manage_requirements import register


@pytest.mark.django_db
@pytest.mark.parametrize("coordinate", ["café", "a+b", "a?b#c", "%2F", "%", "a/b"])
@pytest.mark.parametrize("full_url", [False, True])
def test_uri_coordinates_match_real_requests(client, coordinate, full_url):
    seen = []

    def dispatch(self, request, *args, **kwargs):
        seen.append((request.path_info, kwargs["coordinate"]))
        return super(type(self), self).dispatch(request, *args, **kwargs)

    def build(sfx):
        vs = ViewSet(model=Publisher, name="encoded" + sfx)
        view = register(ListView, vs, dispatch=dispatch, get=lambda self, request, **kw: HttpResponse())
        return view, [vs]

    with isolated_routes(build) as view:
        urlconf = type("URLConf", (), {"urlpatterns": [path("<path:coordinate>/", view.as_view(), name="encoded")]})
        with override_settings(ROOT_URLCONF=urlconf):
            url = reverse("encoded", kwargs={"coordinate": coordinate})
            assert url == "/" + quote(coordinate, safe="/+") + "/"
            if full_url:
                url = "https://unfetched.invalid" + url + "?ignored=yes#fragment"
            assert client.get(url).status_code == 200
            result = trace_access(url, None)
            assert result.outcome == "allowed"
            assert seen == [("/" + coordinate + "/", coordinate)] * 2
            assert result.path == seen[0][0]


@pytest.mark.django_db
def test_reverse_generated_viewset_unicode_paths(client):
    def build(sfx):
        vs = ViewSet(model=Publisher, name="unicoderoute" + sfx, prefix="café")
        register(ListView, vs, get=lambda self, request: HttpResponse())
        return vs, [vs]

    with isolated_routes(build) as vs:
        actor = _user("unicode trace")
        result = ManageView().get_manage_access_trace(vs, actor, mode="viewset")
        row = next(row for row in result["rows"] if row["key"] == "tested")
        assert "%C3%A9" in row["path"]
        assert client.get(row["path"]).status_code == 200
        assert row["trace"]["outcome"] == "allowed"


@pytest.mark.django_db
def test_invalid_utf8_remains_percent_encoded_like_django(client):
    def build(sfx):
        vs = ViewSet(model=Publisher, name="invalidutf" + sfx)
        view = register(ListView, vs, get=lambda self, request: HttpResponse())
        return view, [vs]

    with (
        isolated_routes(build) as view,
        override_settings(ROOT_URLCONF=type("URLConf", (), {"urlpatterns": [path("%FF/", view.as_view())]})),
    ):
        response = client.get("/%FF/")
        assert response.status_code == 200
        result = trace_access("/%FF/", None)
        assert result.outcome == "allowed"
        assert result.path == response.wsgi_request.path_info == "/%FF/"


@pytest.mark.django_db
def test_encoded_object_pk_matches_real_lookup(client):
    def build(sfx):
        vs = ViewSet(model=Publisher, name="encodedpk" + sfx)
        register(DetailView, vs)
        return vs, [vs]

    with isolated_routes(build) as vs:
        obj = Publisher.objects.create(name="encoded PK")
        url = reverse(vs.get_router_name("tested"), kwargs={"pk": obj.pk})
        encoded_pk = "".join(f"%{ord(char):02X}" for char in str(obj.pk))
        url = url.replace(f"/{obj.pk}/", f"/{encoded_pk}/")
        assert client.get(url).status_code == 200
        result = trace_access(url, None)
        assert result.outcome == "allowed"
        assert any(step.object == {"model": "app.publisher", "pk": str(obj.pk)} for step in result.steps)
