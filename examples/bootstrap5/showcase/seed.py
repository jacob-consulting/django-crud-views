from django.contrib.auth import get_user_model

from project.seeding import grant_model_perms
from showcase.models import Recipe

RECIPES = [
    ("Shakshuka", "Eggs poached in spiced tomato sauce.", "easy", 2, True),
    ("Ratatouille", "Slow-simmered vegetable stew.", "medium", 4, False),
    ("Beef Wellington", "Fillet wrapped in mushroom duxelles and puff pastry.", "hard", 6, False),
    ("Pad Thai", "Stir-fried rice noodles with tamarind and peanuts.", "medium", 2, True),
]


def seed():
    User = get_user_model()
    for username in ("alice", "bob"):
        grant_model_perms(User.objects.get(username=username), Recipe)
    for title, description, difficulty, servings, favorite in RECIPES:
        Recipe.objects.get_or_create(
            title=title,
            defaults={
                "description": description,
                "difficulty": difficulty,
                "servings": servings,
                "favorite": favorite,
            },
        )
