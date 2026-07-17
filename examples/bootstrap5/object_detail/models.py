"""
Object Detail example app.

Showcases crud_views_object_detail across all 7 layout packs (accordion, card-rows,
list-group-3col, split-card, striped-rows, table-inline, tabs-vertical) on a single
model, using the ``cv_object_detail_layout`` per-view override so every theme can be
demoed from one project even though the global default pack
(``CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT``) is fixed to "split-card".

PRODUCT_DISPLAY (see views.py) showcases: default rendering for char/text/decimal/
float/integer/boolean/url/date/datetime fields, a badge with color_map+label_map+pill
(``is_active``) and a badge with color_fn (``price``), a property ``link`` (supplier ->
its split-card detail page), a per-type custom ``template`` (a star-rating widget on
``supplier__rating``), FK traversal (``supplier__*``), O2O traversal (``warehouse__*``),
M2M fan-out (``tags``), a model method (``stock_status``), a model @property
(``margin_label``), and a view-computed property (``view_summary``).

Intentionally omitted vs. the upstream django-object-detail catalog example: a
FK->O2O *chain* (e.g. book -> publisher -> publisher.address) and a reverse-O2O
accessor traversal. Warehouse is a direct O2O on Product, so ``warehouse__code`` is a
single-hop O2O traversal, not a two-hop FK->O2O chain — adding that would require a
third model hanging off Supplier or Warehouse, which felt like more model surface than
this app needs to make the point. The single-hop O2O case already exercises the same
resolver code path (``resolve_property``'s ``OneToOneField``/``OneToOneRel`` handling).
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone


class Supplier(models.Model):
    name = models.CharField(max_length=200, help_text="Supplier company name")
    website = models.URLField(blank=True, help_text="Supplier website")
    rating = models.FloatField(default=0.0, help_text="Supplier rating (0-5)")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    code = models.CharField(max_length=20, unique=True)
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=120)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.city})"


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200, help_text="Product name")
    description = models.TextField(blank=True, help_text="Full description")
    sku = models.SlugField(max_length=40, help_text="Stock keeping unit")
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"), help_text="Retail price")
    weight_kg = models.FloatField(default=0.0, help_text="Weight in kilograms")
    stock = models.PositiveIntegerField(default=0, help_text="Units in stock")
    is_active = models.BooleanField(default=True, help_text="Available for sale")
    homepage = models.URLField(blank=True, help_text="Product page")
    release_date = models.DateField(null=True, blank=True, help_text="Release date")
    created_at = models.DateTimeField(default=timezone.now, help_text="Record created")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="products")
    warehouse = models.OneToOneField(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name="product"
    )
    tags = models.ManyToManyField(Tag, related_name="products", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def margin_label(self) -> str:
        return "premium" if self.price >= Decimal("100") else "standard"

    def stock_status(self) -> str:
        return "in stock" if self.stock > 0 else "out of stock"
