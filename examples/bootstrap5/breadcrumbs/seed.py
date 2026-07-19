from django.contrib.auth import get_user_model

from breadcrumbs.models import Board, Workspace
from project.seeding import grant_model_perms

WORKSPACES = {
    "Acme": ["Roadmap", "Sprint Backlog"],
    "Globex": ["Launch Plan", "Support Queue"],
}


def seed():
    User = get_user_model()
    for username in ("alice", "bob"):
        user = User.objects.get(username=username)
        grant_model_perms(user, Workspace)
        grant_model_perms(user, Board)
    for workspace_name, board_titles in WORKSPACES.items():
        workspace, _ = Workspace.objects.get_or_create(name=workspace_name)
        for title in board_titles:
            Board.objects.get_or_create(title=title, workspace=workspace)
