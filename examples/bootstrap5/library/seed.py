from decimal import Decimal

from django.contrib.auth import get_user_model
from project.seeding import grant_model_perms

from library.models import Author, Book

# Enough authors to paginate the table: ListView paginates at 10 by default, so 25 authors
# give three pages (10 / 10 / 5) and a real middle page.
AUTHORS = [
    ("Ursula", "Le Guin", "", [("A Wizard of Earthsea", "7.99"), ("The Dispossessed", "9.99")]),
    ("Terry", "Pratchett", "", [("Guards! Guards!", "8.99"), ("Small Gods", "8.49")]),
    ("Alice", "Sheldon", "James Tiptree Jr.", [("Her Smoke Rose Up Forever", "11.99")]),
    ("Octavia", "Butler", "", [("Kindred", "9.49")]),
    ("Iain", "Banks", "Iain M. Banks", [("The Player of Games", "8.99")]),
    ("Margaret", "Atwood", "", [("The Handmaid's Tale", "9.99")]),
    ("Stanisław", "Lem", "", [("Solaris", "8.49")]),
    ("Ted", "Chiang", "", [("Stories of Your Life and Others", "10.99")]),
    ("N. K.", "Jemisin", "", [("The Fifth Season", "9.99")]),
    ("Douglas", "Adams", "", [("The Hitchhiker's Guide to the Galaxy", "7.49")]),
    ("Mary", "Shelley", "", [("Frankenstein", "5.99")]),
    ("Jules", "Verne", "", [("Twenty Thousand Leagues Under the Seas", "6.99")]),
    ("Isaac", "Asimov", "", [("Foundation", "8.99")]),
    ("Arthur C.", "Clarke", "", [("Childhood's End", "7.99")]),
    ("Philip K.", "Dick", "", [("Ubik", "8.49")]),
    ("Frank", "Herbert", "", [("Dune", "9.99")]),
    ("William", "Gibson", "", [("Neuromancer", "8.99")]),
    ("Liu", "Cixin", "", [("The Three-Body Problem", "10.49")]),
    ("Becky", "Chambers", "", [("The Long Way to a Small, Angry Planet", "9.49")]),
    ("Ann", "Leckie", "", [("Ancillary Justice", "8.99")]),
    ("Ray", "Bradbury", "", [("The Martian Chronicles", "7.99")]),
    ("Connie", "Willis", "", [("Doomsday Book", "9.49")]),
    ("Kim Stanley", "Robinson", "", [("Red Mars", "9.99")]),
    ("Adrian", "Tchaikovsky", "", [("Children of Time", "9.49")]),
    ("Eric Arthur", "Blair", "George Orwell", [("Nineteen Eighty-Four", "6.49")]),
]


def seed():
    user_model = get_user_model()
    for username in ("alice", "bob"):
        user = user_model.objects.get(username=username)
        grant_model_perms(user, Author)
        grant_model_perms(user, Book)
    for first, last, pseudonym, books in AUTHORS:
        author, _ = Author.objects.get_or_create(first_name=first, last_name=last, defaults={"pseudonym": pseudonym})
        for title, price in books:
            Book.objects.get_or_create(title=title, author=author, defaults={"price": Decimal(price)})
