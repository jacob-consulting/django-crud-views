from django.contrib.auth import get_user_model
from project.seeding import grant_model_perms

from showcase.models import Recipe

# Enough recipes to paginate the card list: RecipeCardListView shows six per page, so 14 recipes
# give three pages (6 / 6 / 2) and a real middle page.
RECIPES = [
    ("Shakshuka", "Eggs poached in spiced tomato sauce.", "easy", 2, True),
    ("Ratatouille", "Slow-simmered vegetable stew.", "medium", 4, False),
    ("Beef Wellington", "Fillet wrapped in mushroom duxelles and puff pastry.", "hard", 6, False),
    ("Pad Thai", "Stir-fried rice noodles with tamarind and peanuts.", "medium", 2, True),
    ("Margherita Pizza", "Tomato, mozzarella and basil on a thin crust.", "easy", 2, True),
    ("Coq au Vin", "Chicken braised slowly in red wine with mushrooms.", "hard", 4, False),
    ("Dal Tadka", "Yellow lentils finished with spiced ghee.", "easy", 4, False),
    ("Risotto ai Funghi", "Creamy rice with porcini and parmesan.", "medium", 3, True),
    ("Bibimbap", "Rice bowl with vegetables, egg and gochujang.", "medium", 2, False),
    ("Falafel Wraps", "Crisp chickpea fritters in flatbread with tahini.", "easy", 3, False),
    ("Bouillabaisse", "Provençal fish stew with saffron and fennel.", "hard", 6, False),
    ("Gazpacho", "Chilled tomato and cucumber soup.", "easy", 4, True),
    ("Lamb Tagine", "Lamb stewed with apricots and warm spices.", "medium", 5, False),
    ("Soufflé au Fromage", "Airy baked cheese soufflé.", "hard", 2, False),
]


def seed():
    user_model = get_user_model()
    for username in ("alice", "bob"):
        grant_model_perms(user_model.objects.get(username=username), Recipe)
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
