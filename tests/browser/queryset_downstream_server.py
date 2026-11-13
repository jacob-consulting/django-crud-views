"""Disposable roastery host: real downstream settings, routes and assets, pinned upstream.

No developer SQLite or media is opened. Fixture writes require loopback, login,
the per-run secret, and ordinary Django CSRF verification.
"""

# ruff: noqa: E402
import importlib
import json
import os
import platform
import sys
from pathlib import Path
from wsgiref.simple_server import make_server

import django

UPSTREAM = Path(os.environ["CV_QUERYSET_UPSTREAM"]).resolve()
DOWNSTREAM = Path(os.environ["CV_QUERYSET_DOWNSTREAM"]).resolve()
TEMP = Path(os.environ["CV_QUERYSET_TEMP"]).resolve()
assert TEMP.name.startswith("cv-queryset-") and TEMP.is_dir()
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
from django.conf import settings

assert Path(importlib.import_module("config.settings").__file__).resolve() == DOWNSTREAM / "example/config/settings.py"
settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": str(TEMP / "db.sqlite3")}}
settings.MEDIA_ROOT = TEMP / "media"
settings.ALLOWED_HOSTS = ["127.0.0.1"]
settings.ROOT_URLCONF = __name__
django.setup()

from catalog.models import Beans, Equipment, Origin, Product, Subscription
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.db import connection
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import include, path, reverse
from sales.models import Customer, Order, OrderLine

import crud_views

assert Path(crud_views.__file__).resolve() == UPSTREAM / "src/crud_views/__init__.py"
call_command("migrate", verbosity=0, interactive=False)
user = get_user_model().objects.create_superuser(username="browser", password="browser-only-password", email="")
customer = Customer.objects.create(name="Browser customer", owner=user)
origin = Origin.objects.create(country="CO", region="Browser")
write_count = 0


class WriteAudit:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        def audit(execute, sql, params, many, context):
            global write_count
            if sql.lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE"} and any(
                model._meta.db_table in sql for model in (Order, OrderLine)
            ):
                write_count += 1
            return execute(sql, params, many, context)

        if request.path.startswith("/__fixture__/"):
            return self.get_response(request)
        with connection.execute_wrapper(audit):
            return self.get_response(request)


settings.MIDDLEWARE = [*settings.MIDDLEWARE, "__main__.WriteAudit"]
products = {}
for name, klass, attributes in (
    ("coffee", Beans, {"origin": origin}),
    ("retired", Beans, {"origin": origin, "is_active": False}),
    ("equipment", Equipment, {"brand": "Browser"}),
    ("subscription", Subscription, {}),
):
    products[name] = klass.objects.create(name=name, slug=name, sku=name, price="10.00", **attributes)
fixtures = {}
for name, choices in (
    ("order", ["coffee", "equipment"]),
    ("retained", ["retired", "subscription"]),
    ("mutation", ["coffee", "equipment"]),
    ("unchanged", ["equipment", "subscription"]),
):
    order = Order.objects.create(customer=customer)
    fixtures[name] = order.pk
    for choice in choices:
        OrderLine.objects.create(
            order=order,
            product=products[choice],
            quantity=1,
            grind="espresso" if choice in ("coffee", "retired") else "",
            bag_size="1kg" if choice in ("coffee", "retired") else "",
        )


@login_required
def state(request):
    if (
        request.META.get("REMOTE_ADDR") != "127.0.0.1"
        or not request.user.is_superuser
        or request.headers.get("X-Fixture-Key") != os.environ["CV_QUERYSET_SECRET"]
    ):
        return HttpResponseForbidden()
    if request.method == "POST":
        data = json.loads(request.body)
        if data["operation"] == "active" and data["pk"] in [p.pk for p in products.values()]:
            Product.objects.filter(pk=data["pk"]).update(is_active=data["active"])
        elif data["operation"] == "stale":
            OrderLine.objects.filter(order_id=fixtures["unchanged"]).update(grind="filter", bag_size="250g")
        else:
            return HttpResponseForbidden()
    return JsonResponse(
        {
            "runtime": {
                "python": platform.python_version(),
                "django": django.get_version(),
                "pythonPath": sys.executable,
                "settings": "config.settings",
                "source": str(Path(crud_views.__file__).resolve()),
            },
            "urls": {
                **{
                    name: reverse("order-update", kwargs={"customer_pk": customer.pk, "pk": pk})
                    for name, pk in fixtures.items()
                },
                "create": reverse("order-create", kwargs={"customer_pk": customer.pk}),
                "print": reverse("order-packing_slip", kwargs={"customer_pk": customer.pk, "pk": fixtures["order"]}),
            },
            "products": {name: obj.pk for name, obj in products.items()},
            "writes": write_count,
            "fixtures": fixtures,
            "types": list(
                Product.objects.non_polymorphic().order_by("pk").values("pk", "polymorphic_ctype_id", "is_active")
            ),
            "orders": list(Order.objects.order_by("pk").values()),
            "lines": list(OrderLine.objects.order_by("pk").values()),
        }
    )


urlpatterns = [path("__fixture__/state/", state), path("", include("config.urls"))]
with make_server("127.0.0.1", 0, StaticFilesHandler(get_wsgi_application())) as server:
    print(json.dumps({"port": server.server_port, "temporary": str(TEMP), "login": reverse("login")}), flush=True)
    server.serve_forever()
