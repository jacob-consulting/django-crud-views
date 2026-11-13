from django.contrib.auth import get_user_model
from project.seeding import check_developer_object_permissions, grant_model_perms

from guardian_demo.models import Document, Note
from guardian_demo.views import cv_document, cv_note

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

#: document title → notes as (author username, text)
NOTES = {
    "Team Handbook": [("alice", "Added the onboarding checklist.")],
    "Release Checklist": [
        ("bob", "Tag the release before publishing."),
        ("alice", "Changelog reviewed."),
    ],
}


def seed():
    user_model = get_user_model()
    users = {name: user_model.objects.get(username=name) for name in ("alice", "bob")}
    developer = user_model.objects.get(username="developer")
    for user in users.values():
        grant_model_perms(user, Document, actions=("add",))

    docs = {}
    for username, documents in DOCUMENTS.items():
        owner = users[username]
        for title, body in documents:
            doc, _ = Document.objects.get_or_create(title=title, defaults={"body": body, "owner": owner})
            check_developer_object_permissions(developer, doc)
            cv_document.assign_perm("view", developer, doc)
            docs[title] = doc
            for action in ("view", "change", "delete"):
                cv_document.assign_perm(action, owner, doc)

    # alice shares the handbook with bob, view-only
    cv_document.assign_perm("view", users["bob"], docs["Team Handbook"])
    # bob shares the release checklist with alice: she may edit it, not delete it
    for action in ("view", "change"):
        cv_document.assign_perm(action, users["alice"], docs["Release Checklist"])

    # notes: whoever may view a document may view its notes; only the author and the document owner edit them
    for title, notes in NOTES.items():
        doc = docs[title]
        for username, text in notes:
            note, _ = Note.objects.get_or_create(document=doc, author=users[username], text=text)
            check_developer_object_permissions(developer, note)
            cv_note.assign_perm("view", developer, note)
            for user in {note.author, doc.owner}:
                for action in ("view", "change", "delete"):
                    cv_note.assign_perm(action, user, note)
    # the two document shares extend to their notes, read-only
    for note in docs["Team Handbook"].notes.all():
        cv_note.assign_perm("view", users["bob"], note)
    for note in docs["Release Checklist"].notes.all():
        cv_note.assign_perm("view", users["alice"], note)
