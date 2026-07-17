from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from object_detail.models import Product, Supplier, Tag, Warehouse
from project.seeding import grant_model_perms

SUPPLIERS = [
    ("Acme Corp", "https://acme.example.com", 4.5),
    ("Globex", "https://globex.example.com", 3.8),
]

WAREHOUSES = [
    ("W-EU-01", "Berlin", "Germany"),
    ("W-US-01", "Portland", "USA"),
]

TAGS = ["electronics", "outdoor", "sale", "featured"]

# (name, sku, description, price, weight_kg, stock, is_active, homepage, supplier_idx, warehouse_idx, tags)
PRODUCTS = [
    (
        "Trail Runner Backpack",
        "trail-runner-backpack",
        "Lightweight 28L backpack for day hikes.",
        Decimal("129.00"),
        1.2,
        42,
        True,
        "https://example.com/products/trail-runner-backpack",
        0,
        0,
        ["outdoor", "featured"],
    ),
    (
        "Wireless Earbuds Pro",
        "wireless-earbuds-pro",
        "Noise-cancelling earbuds with 30h battery.",
        Decimal("89.99"),
        0.05,
        150,
        True,
        "https://example.com/products/wireless-earbuds-pro",
        1,
        1,
        ["electronics", "sale"],
    ),
    (
        "Desk Lamp Mini",
        "desk-lamp-mini",
        "",
        Decimal("19.50"),
        0.4,
        0,
        False,
        "",
        0,
        None,
        ["electronics"],
    ),
]


def seed():
    User = get_user_model()
    for username in ("alice", "bob"):
        user = User.objects.get(username=username)
        grant_model_perms(user, Product)
        grant_model_perms(user, Supplier)

    suppliers = [
        Supplier.objects.get_or_create(name=name, defaults={"website": website, "rating": rating})[0]
        for name, website, rating in SUPPLIERS
    ]
    warehouses = [
        Warehouse.objects.get_or_create(code=code, defaults={"city": city, "country": country})[0]
        for code, city, country in WAREHOUSES
    ]
    tags = {name: Tag.objects.get_or_create(name=name)[0] for name in TAGS}

    for (
        name,
        sku,
        description,
        price,
        weight_kg,
        stock,
        is_active,
        homepage,
        supplier_idx,
        warehouse_idx,
        tag_names,
    ) in PRODUCTS:
        product, _ = Product.objects.get_or_create(
            sku=sku,
            defaults={
                "name": name,
                "description": description,
                "price": price,
                "weight_kg": weight_kg,
                "stock": stock,
                "is_active": is_active,
                "homepage": homepage,
                "release_date": timezone.now().date(),
                "supplier": suppliers[supplier_idx],
                "warehouse": warehouses[warehouse_idx] if warehouse_idx is not None else None,
            },
        )
        product.tags.set([tags[t] for t in tag_names])
