from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from polymorphic_demo.models import Car, Motorcycle, Truck, Vehicle


class PolymorphicTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")
        cls.car = Car.objects.create(name="Coupe", doors=2)
        cls.truck = Truck.objects.create(name="Hauler", payload_tons=7)
        cls.bike = Motorcycle.objects.create(name="Roadster", engine_cc=900)

    def setUp(self):
        self.client.force_login(self.admin)


class VehicleListTest(PolymorphicTestCase):
    def test_list_shows_all_subtypes_with_snippets(self):
        resp = self.client.get(reverse("vehicle-list"))
        self.assertEqual(resp.status_code, 200)
        for name in ("Coupe", "Hauler", "Roadster"):
            self.assertContains(resp, name)
        self.assertContains(resp, "snippet-panels")


class VehicleCreateSelectTest(PolymorphicTestCase):
    def test_select_redirects_to_typed_create(self):
        car_ct = ContentType.objects.get_for_model(Car)
        resp = self.client.post("/polymorphic/vehicle/create/select/", {"polymorphic_ctype_id": car_ct.id})
        self.assertEqual(resp.status_code, 302)
        self.assertIn(f"/ct/{car_ct.id}/", resp.url)

    def test_create_car_through_typed_form(self):
        car_ct = ContentType.objects.get_for_model(Car)
        resp = self.client.post(f"/polymorphic/vehicle/create//ct/{car_ct.id}/", {"name": "Family Van", "doors": 5})
        self.assertEqual(resp.status_code, 302)
        car = Car.objects.get(name="Family Van")
        self.assertEqual(car.doors, 5)
        self.assertTrue(Vehicle.objects.filter(pk=car.pk).exists())

    def test_detail_of_subtype(self):
        resp = self.client.get(reverse("vehicle-detail", kwargs={"pk": self.truck.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Hauler")


class PolymorphicSeedTest(TestCase):
    def test_seed_twice_and_covers_all_types(self):
        from django.core.management import call_command

        call_command("seed")
        count = Vehicle.objects.count()
        call_command("seed")
        self.assertEqual(Vehicle.objects.count(), count)
        self.assertTrue(Car.objects.exists())
        self.assertTrue(Truck.objects.exists())
        self.assertTrue(Motorcycle.objects.exists())
