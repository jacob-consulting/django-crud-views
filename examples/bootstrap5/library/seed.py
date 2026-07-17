from decimal import Decimal

from django.contrib.auth import get_user_model

from library.models import Author, Book
from project.seeding import grant_model_perms

AUTHORS = [
    ("Ursula", "Le Guin", None, [("A Wizard of Earthsea", "7.99"), ("The Dispossessed", "9.99")]),
    ("Terry", "Pratchett", None, [("Guards! Guards!", "8.99"), ("Small Gods", "8.49")]),
    ("Alice", "Sheldon", "James Tiptree Jr.", [("Her Smoke Rose Up Forever", "11.99")]),
]


def seed():
    User = get_user_model()
    for username in ("alice", "bob"):
        user = User.objects.get(username=username)
        grant_model_perms(user, Author)
        grant_model_perms(user, Book)
    for first, last, pseudonym, books in AUTHORS:
        author, _ = Author.objects.get_or_create(first_name=first, last_name=last, defaults={"pseudonym": pseudonym})
        for title, price in books:
            Book.objects.get_or_create(title=title, author=author, defaults={"price": Decimal(price)})
