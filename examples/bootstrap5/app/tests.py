"""Smoke test for the view-level context button on BarDetailView (issue #27 example)."""

import warnings

from django.contrib.auth.models import User
from django.core.paginator import UnorderedObjectListWarning
from django.test import TestCase
from django.urls import reverse

from app.models import Foo, Bar, Baz
from app.views.bar import cv_bar
from app.views.baz import cv_baz


class ViewLevelContextButtonTest(TestCase):
    def setUp(self):
        self.foo = Foo.objects.create(name="Foo1")
        self.bar = Bar.objects.create(foo=self.foo, name="Bar1")
        self.baz = Baz.objects.create(bar=self.bar, name="Baz1")
        user = User.objects.create_superuser(username="admin", password="pw")
        self.client.force_login(user)

    def test_bazzes_button_on_bar_detail(self):
        url = reverse(cv_bar.get_router_name("detail"), kwargs={"foo_pk": self.foo.pk, "pk": self.bar.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # the view-level "Bazzes" button appears on the detail page...
        self.assertContains(resp, "Bazzes")
        # ...and links to this bar's baz collection
        baz_url = reverse(cv_baz.get_router_name("list"), kwargs={"foo_pk": self.foo.pk, "bar_pk": self.bar.pk})
        self.assertContains(resp, baz_url)

    def test_bazzes_absent_on_bar_list(self):
        url = reverse(cv_bar.get_router_name("list"), kwargs={"foo_pk": self.foo.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # the view-level button does NOT leak onto the list view...
        self.assertNotContains(resp, "Bazzes")
        # ...which still shows the ViewSet-level sibling button
        self.assertContains(resp, "Quxes")

    def test_bar_list_pagination_is_ordered(self):
        # Paginating an unordered queryset raises UnorderedObjectListWarning; the Bar
        # model's Meta.ordering must keep the list view's pagination stable.
        url = reverse(cv_bar.get_router_name("list"), kwargs={"foo_pk": self.foo.pk})
        with warnings.catch_warnings():
            warnings.simplefilter("error", UnorderedObjectListWarning)
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
