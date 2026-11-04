from django.contrib.auth import get_user_model
from guardian.shortcuts import assign_perm
from project.seeding import grant_model_perms

from delete_demo.models import Milestone, Project, Task
from delete_demo.views import cv_project, cv_task

OBJECT_ACTIONS = ("view", "change", "delete")

#: project title → (owner, is_shared, milestone titles, [(task title, task owner), ...])
PROJECTS = {
    # blocked: alice's own tasks protect the project, she sees their titles
    "Website relaunch": ("alice", False, [], [("Draft the sitemap", "alice"), ("Pick a new theme", "alice")]),
    # blocked by objects alice cannot see: bob's task, no grant to alice
    "Office move": ("alice", False, [], [("Book the movers", "bob")]),
    # blocked by the business rule in ProjectDeleteView.cv_check_delete_protection
    "Annual report": ("alice", True, [], []),
    # deletable: the confirmation page previews the milestones deleted with it
    "Old prototype": ("alice", False, ["Clickable mockup", "User test round"], []),
    # bob's own project, so his list is not empty
    "Garden shed": ("bob", False, [], [("Buy timber", "bob")]),
}


def seed():
    user_model = get_user_model()
    users = {name: user_model.objects.get(username=name) for name in ("alice", "bob")}
    for user in users.values():
        grant_model_perms(user, Project, actions=("add",))

    for title, (owner_name, is_shared, milestones, tasks) in PROJECTS.items():
        owner = users[owner_name]
        project, _ = Project.objects.get_or_create(title=title, defaults={"owner": owner, "is_shared": is_shared})
        for action in OBJECT_ACTIONS:
            cv_project.assign_perm(action, owner, project)
        for milestone_title in milestones:
            milestone, _ = Milestone.objects.get_or_create(project=project, title=milestone_title)
            # Milestone has no ViewSet; the grant lets the delete preview show its title
            assign_perm("delete_demo.view_milestone", owner, milestone)
        for task_title, task_owner_name in tasks:
            task_owner = users[task_owner_name]
            task, _ = Task.objects.get_or_create(project=project, title=task_title, defaults={"owner": task_owner})
            for action in OBJECT_ACTIONS:
                cv_task.assign_perm(action, task_owner, task)
