import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from object_detail.models import Product
from object_detail.seed import seed
from object_detail.views import THEMES, detail_url_name
from project.seeding import ensure_demo_users

# Discriminating marker per layout pack, copied from tests/test1/od/test_layout_packs.py
# (LAYOUT_PACKS): a substring that appears in exactly one pack's templates and is rendered
# unconditionally by that pack's group.html, so a match proves the right pack actually
# rendered instead of a pack-agnostic fallback.
LAYOUT_MARKERS = {
    "split-card": "border-end",
    "card-rows": 'data-bs-toggle="tooltip"',
    "table-inline": "table table-borderless mb-0",
    "list-group-3col": "list-group-item",
    "accordion": "accordion-item",
    "tabs-vertical": "tab-pane",
    "striped-rows": "table-striped",
}


@pytest.fixture
def seeded():
    ensure_demo_users()
    seed()
    return {
        "product": Product.objects.get(sku="trail-runner-backpack"),
        "user": get_user_model().objects.get(username="alice"),
    }


@pytest.fixture
def seeded_product(seeded):
    return seeded["product"]


@pytest.fixture
def alice_client(client, seeded):
    client.force_login(seeded["user"])
    return client


@pytest.mark.django_db
@pytest.mark.parametrize("theme", THEMES)
def test_product_detail_theme_renders(alice_client, seeded_product, theme):
    url = reverse(detail_url_name(theme), kwargs={"pk": seeded_product.pk})
    response = alice_client.get(url)
    assert response.status_code == 200
    assert LAYOUT_MARKERS[theme] in response.content.decode()


@pytest.mark.django_db
def test_product_list_renders(alice_client):
    response = alice_client.get(reverse("product-list"))
    assert response.status_code == 200
    assert "Trail Runner Backpack" in response.content.decode()


@pytest.mark.django_db
def test_supplier_detail_renders(alice_client, seeded_product):
    response = alice_client.get(reverse("supplier-detail", kwargs={"pk": seeded_product.supplier_id}))
    assert response.status_code == 200
    assert "Acme Corp" in response.content.decode()
