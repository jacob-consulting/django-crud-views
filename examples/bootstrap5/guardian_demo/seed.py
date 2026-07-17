from django.contrib.auth import get_user_model

from guardian_demo.models import Document
from guardian_demo.views import cv_document
from project.seeding import grant_model_perms

#: owner username → documents
DOCUMENTS = {
    "alice": [
        ("Roadmap 2027", "Where the product is heading."),
        ("Team Handbook", "How we work together."),
    ],
    "bob": [
        ("Meeting Notes", "Standup summaries."),
    ],
}


def seed():
    User = get_user_model()
    users = {name: User.objects.get(username=name) for name in ("alice", "bob")}
    for user in users.values():
        grant_model_perms(user, Document, actions=("add",))

    docs = {}
    for username, documents in DOCUMENTS.items():
        owner = users[username]
        for title, body in documents:
            doc, _ = Document.objects.get_or_create(title=title, defaults={"body": body, "owner": owner})
            docs[title] = doc
            for action in ("view", "change", "delete"):
                cv_document.assign_perm(action, owner, doc)

    # alice shares the handbook with bob, view-only
    cv_document.assign_perm("view", users["bob"], docs["Team Handbook"])
