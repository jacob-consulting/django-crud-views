"""
Object Detail example app.

Showcases crud_views_object_detail across all 7 layout packs (accordion, card-rows,
list-group-3col, split-card, striped-rows, table-inline, tabs-vertical) on a single
model, using the ``cv_object_detail_layout`` per-view override so every theme can be
demoed from one project even though the global default pack
(``CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT``) is fixed to "split-card".

PRODUCT_DISPLAY (see views.py) showcases: default rendering for char/text/decimal/
float/integer/boolean/url/date/datetime fields, a badge with color_map+label_map+pill
(``is_active``) and a badge with color_fn (``price``), a property ``link`` (``supplier``
-> that Supplier's OWN detail page, via the minimal ``cv_supplier`` ViewSet added purely
as a correct link target), a per-type custom ``template`` (a star-rating widget on
``supplier__rating``), FK traversal (``supplier__*``), O2O traversal (``warehouse__*``),
M2M fan-out (``tags``), a model method (``stock_status``), a model @property
(``margin_label``), and a view-computed property (``view_summary``). The plain
``BadgeConfig.color`` variant is showcased on the Supplier detail page's ``rating``
property (see ``SupplierDetailView`` in views.py) rather than on Product.

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
from django.utils.translation import gettext_lazy as _


class Supplier(models.Model):
    name = models.CharField(_("name"), max_length=200, help_text=_("Supplier company name"))
    website = models.URLField(_("website"), blank=True, help_text=_("Supplier website"))
    rating = models.FloatField(_("rating"), default=0.0, help_text=_("Supplier rating (0-5)"))

    class Meta:
        ordering = ["name"]
        verbose_name = _("supplier")
        verbose_name_plural = _("suppliers")

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    code = models.CharField(_("code"), max_length=20, unique=True)
    city = models.CharField(_("city"), max_length=120)
    country = models.CharField(_("country"), max_length=120)

    class Meta:
        ordering = ["code"]
        verbose_name = _("warehouse")
        verbose_name_plural = _("warehouses")

    def __str__(self):
        return f"{self.code} ({self.city})"


class Tag(models.Model):
    name = models.CharField(_("name"), max_length=60, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("tag")
        verbose_name_plural = _("tags")

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(_("name"), max_length=200, help_text=_("Product name"))
    description = models.TextField(_("description"), blank=True, help_text=_("Full description"))
    sku = models.SlugField(_("SKU"), max_length=40, help_text=_("Stock keeping unit"))
    price = models.DecimalField(
        _("price"), max_digits=8, decimal_places=2, default=Decimal("0.00"), help_text=_("Retail price")
    )
    weight_kg = models.FloatField(_("weight (kg)"), default=0.0, help_text=_("Weight in kilograms"))
    stock = models.PositiveIntegerField(_("stock"), default=0, help_text=_("Units in stock"))
    is_active = models.BooleanField(_("active"), default=True, help_text=_("Available for sale"))
    homepage = models.URLField(_("homepage"), blank=True, help_text=_("Product page"))
    release_date = models.DateField(_("release date"), null=True, blank=True, help_text=_("Release date"))
    created_at = models.DateTimeField(_("created"), default=timezone.now, help_text=_("Record created"))
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="products", verbose_name=_("supplier")
    )
    warehouse = models.OneToOneField(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product",
        verbose_name=_("warehouse"),
    )
    tags = models.ManyToManyField(Tag, related_name="products", blank=True, verbose_name=_("tags"))

    class Meta:
        ordering = ["name"]
        verbose_name = _("product")
        verbose_name_plural = _("products")

    def __str__(self):
        return self.name

    @property
    def margin_label(self) -> str:
        return _("premium") if self.price >= Decimal("100") else _("standard")

    def stock_status(self) -> str:
        return _("in stock") if self.stock > 0 else _("out of stock")
