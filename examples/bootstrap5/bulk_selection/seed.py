from django.contrib.auth import get_user_model
from project.seeding import grant_model_perms

from bulk_selection.models import Document

DOCUMENTS = [
    ("Document 01", "draft", False),
    ("Document 02", "draft", False),
    ("Document 03", "draft", True),
    ("Document 04", "draft", False),
    ("Document 05", "published", False),
    ("Document 06", "draft", False),
    ("Document 07", "draft", False),
    ("Document 08", "draft", False),
    ("Document 09", "draft", True),
    ("Document 10", "draft", False),
    ("Document 11", "draft", False),
    ("Document 12", "draft", False),
    ("Document 13", "draft", False),
    ("Document 14", "draft", False),
    ("Document 15", "draft", False),
    ("Document 16", "draft", False),
    ("Document 17", "published", False),
    ("Document 18", "draft", False),
    ("Document 19", "draft", False),
    ("Document 20", "draft", False),
    ("Document 21", "draft", False),
    ("Document 22", "draft", False),
    ("Document 23", "draft", False),
    ("Document 24", "draft", False),
]


def seed():
    user_model = get_user_model()
    for username in ("alice", "bob"):
        grant_model_perms(
            user_model.objects.get(username=username), Document, actions=("view", "add", "change", "delete")
        )
    for title, status, is_locked in DOCUMENTS:
        Document.objects.get_or_create(title=title, defaults={"status": status, "is_locked": is_locked})
