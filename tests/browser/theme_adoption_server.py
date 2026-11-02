"""Isolated real Tabler source preparation and authenticated loopback acceptance server."""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import theme_adoption_sources as sources  # noqa: E402


def current_core():
    return {
        p.relative_to(ROOT).as_posix(): p.read_bytes()
        for base in (ROOT / "src", ROOT / "tests", ROOT / "docs")
        for p in base.rglob("*")
        if p.is_file() and not p.is_symlink() and not set(p.parts) & sources.RUNTIME_EXCLUDES
    } | {
        name: (ROOT / name).read_bytes()
        for name in ("pyproject.toml", "package.json", "package-lock.json")
        if (ROOT / name).is_file()
    }


def prepare(target, delivered=None):
    baseline = sources.load_json(ROOT / sources.PHASE_DIR / sources.BASELINE_NAME)
    sources.check_baseline(baseline)
    original = sources.resolve_recorded_source(delivered or "recorded", manifest=baseline)
    before = sources.preservation(original)
    files = sources.archive_files(original, baseline["revision"])
    if delivered:
        # Read only tracked public bytes; private settings always come from the pinned archive.
        for name in files:
            if name != "example/config/settings.py":
                files[name] = (original / name).read_bytes()
    core_files = current_core()
    core = Path(target) / "django-crud-views"
    companion = Path(target) / "tabler-test"
    sources.write_tree(core_files, core)
    sources.write_tree(files, companion)
    executable = sources.resolve_companion_python(baseline)
    origins, command = sources.probe_origins(executable, companion, core, files, core_files)
    sources.require(sources.preservation(original) == before, "original changed during preparation")
    return {
        "core": str(core),
        "companion": str(companion),
        "env": {key: value for key, value in sources.isolated_env(companion, core).items()
                if key in {"PYTHONPATH", "DJANGO_SETTINGS_MODULE", "DJANGO_SECRET_KEY", "DJANGO_DEBUG", "DJANGO_ALLOWED_HOSTS"}},
        "source_sha256": sources.digest(sources.inventory(files)),
        "core_inventory": sources.inventory(core_files),
        "origins": origins,
        "origin_command": command,
        "preserved": before,
        "runtime": baseline["runtime"],
    }


def serve():
    sys.path.insert(0, str(ROOT))
    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    text = os.environ.get("CV_THEME_PORT", "8145")
    if not re.fullmatch(r"[0-9]+", text) or not 1024 <= int(text) <= 65535 or int(text) in (8143, 8144):
        raise SystemExit("CV_THEME_PORT must be decimal 1024..65535; reserved ports: 8143, 8144")
    import signal
    import tempfile
    from html.parser import HTMLParser
    from unittest.mock import patch
    from wsgiref.simple_server import make_server

    from django.conf import settings

    temporary = tempfile.TemporaryDirectory(prefix="dcv-theme-db-")
    configure = settings.configure

    def themed_configure(self, **kwargs):
        kwargs["INSTALLED_APPS"][0:0] = ["django_tabler", "crud_views_tabler", "django.contrib.humanize"]
        kwargs["INSTALLED_APPS"] += ["dashboard", "catalog", "customers"]
        kwargs["CRUD_VIEWS_EXTENDS"] = "crud_views_tabler/page.html"
        kwargs["CRISPY_TEMPLATE_PACK"] = "crispy_tabler"
        kwargs["CRISPY_ALLOWED_TEMPLATE_PACKS"] = ["crispy_tabler"]
        kwargs["DATABASES"]["default"]["NAME"] = str(Path(temporary.name) / "db.sqlite3")
        kwargs["ALLOWED_HOSTS"] = ["127.0.0.1", "testserver"]
        kwargs["ROOT_URLCONF"] = __name__
        kwargs["TEMPLATES"][0]["DIRS"] = []
        configure(**kwargs)

    from tests.test1.conftest import pytest_configure

    with patch.object(type(settings), "configure", themed_configure):
        pytest_configure()

    from django.contrib.auth import login
    from django.contrib.auth.models import User
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from django.db import connection
    from django.http import HttpResponse, JsonResponse
    from django.middleware.csrf import get_token
    from django.template import Template
    from django.urls import include, path

    from tests.test1.app.views import AuthorCreateView

    call_command("migrate", run_syncdb=True, verbosity=0)
    actor = User.objects.create_superuser(username="theme-browser", password=None, email="")
    observations = {"last": None, "history": []}

    class Forms(HTMLParser):
        def __init__(self):
            super().__init__()
            self.forms = []
            self.stack = []
            self.nested = []

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "form":
                if self.stack:
                    self.nested.append(attrs)
                form = {"attrs": attrs, "tokens": 0}
                self.forms.append(form)
                self.stack.append(form)
            if tag == "input" and attrs.get("name") == "csrfmiddlewaretoken" and self.stack:
                self.stack[-1]["tokens"] += 1

        def handle_endtag(self, tag):
            if tag == "form" and self.stack:
                self.stack.pop()

    def observed(request, view, **kwargs):
        templates = []
        render = Template._render

        def record(template, context):
            templates.append({"name": template.name, "origin": template.origin.name})
            return render(template, context)

        with patch.object(Template, "_render", record):
            response = view.as_view()(request, **kwargs)
            if hasattr(response, "render"):
                response.render()
        if response.status_code == 200 and "text/html" in response.get("Content-Type", ""):
            html = response.content.decode()
            token = get_token(request)
            auxiliary = "".join(
                f'<form id="aux-{name}" method="post"><input name="csrfmiddlewaretoken" value="{token}">'
                f'<input name="{name}"><button>{name}</button></form>'
                for name in ("search", "action")
            )
            response.content = html.replace("</body>", auxiliary + "</body>")
            parsed = Forms()
            parsed.feed(response.content.decode())
            row = {"route": request.path, "method": request.method, "templates": templates,
                   "forms": parsed.forms, "nested": parsed.nested}
            observations["last"] = row
            observations["history"].append(row)
        return response

    def signin(request):
        login(request, actor, backend="django.contrib.auth.backends.ModelBackend")
        return JsonResponse({"signed_in": True})

    globals()["urlpatterns"] = [
        path("signin/", signin),
        path("create/", lambda request: observed(request, AuthorCreateView)),
        path("observations/", lambda request: JsonResponse(observations)),
        path("favicon.ico", lambda request: HttpResponse(status=204)),
        path("", include("tests.test1.project.urls")),
        path("", include("config.urls")),
    ]
    try:
        with make_server("127.0.0.1", int(text), StaticFilesHandler(get_wsgi_application())) as server:
            def stop(signum, frame):
                raise SystemExit(0)

            signal.signal(signal.SIGTERM, stop)
            print(json.dumps({"ready": int(text)}), flush=True)
            server.serve_forever()
    finally:
        connection.close()
        temporary.cleanup()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare")
    parser.add_argument("--delivered-source")
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(prepare(args.prepare, args.delivered_source)))
    elif args.serve:
        serve()


if __name__ == "__main__":
    main()
