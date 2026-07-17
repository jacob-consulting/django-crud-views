from django.contrib.auth import get_user_model

from polymorphic_demo.models import Car, Motorcycle, Truck, Vehicle
from project.seeding import grant_model_perms


def seed():
    User = get_user_model()
    for username in ("alice", "bob"):
        user = User.objects.get(username=username)
        for model in (Vehicle, Car, Truck, Motorcycle):
            grant_model_perms(user, model)
    Car.objects.get_or_create(name="Coupe", defaults={"doors": 2})
    Car.objects.get_or_create(name="Family Van", defaults={"doors": 5})
    Truck.objects.get_or_create(name="Hauler", defaults={"payload_tons": 7})
    Motorcycle.objects.get_or_create(name="Roadster", defaults={"engine_cc": 900})
