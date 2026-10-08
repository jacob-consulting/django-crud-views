from django.contrib.auth import get_user_model
from project.seeding import grant_model_perms

from guardian_demo.models import Document
from guardian_demo.views import cv_document

#: owner username → documents
DOCUMENTS = {
    "alice": [
        ("Roadmap 2027", "Where the product is heading."),
        ("Team Handbook", "How we work together."),
    ],
    "bob": [
        ("Meeting Notes", "Standup summaries."),
        ("Release Checklist", "Steps before every release."),
    ],
}


def seed():
    user_model = get_user_model()
    users = {name: user_model.objects.get(username=name) for name in ("alice", "bob")}
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
    # bob shares the release checklist with alice: she may edit it, not delete it
    for action in ("view", "change"):
        cv_document.assign_perm(action, users["alice"], docs["Release Checklist"])
