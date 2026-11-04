import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from crud_views.lib.crispy import Column6, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import ListViewTableMixin, MessageMixin
from crud_views_guardian.lib.views import (
    GuardianCreateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianListViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
)
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_object_detail.lib import ObjectDetailMixin
from delete_demo.models import Project, Task

cv_project = GuardianViewSet(model=Project, name="project", icon_header="fa-solid fa-diagram-project")
cv_task = GuardianViewSet(model=Task, name="task", icon_header="fa-solid fa-list-check")


class ProjectForm(CrispyModelForm):
    class Meta:
        model = Project
        fields = ["title", "is_shared"]

    def get_layout_fields(self):
        return [Row(Column6("title")), Row(Column6("is_shared"))]


class ProjectTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()
    owner = tables.Column()
    is_shared = tables.BooleanColumn()


class ProjectListView(BreadcrumbMixin, ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_project
    table_class = ProjectTable


class ProjectDetailView(BreadcrumbMixin, ObjectDetailMixin, GuardianDetailViewPermissionRequired):
    cv_viewset = cv_project
    cv_property_display = [
        {"title": _("Project"), "icon": "fas:diagram-project", "properties": ["id", "title", "owner", "is_shared"]},
    ]


class ProjectCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, GuardianCreateViewPermissionRequired):
    cv_viewset = cv_project
    form_class = ProjectForm
    cv_message_template_code = _("Created project “{{ object }}”")

    def cv_form_valid(self, context: dict):
        # the creator owns the project and gets full object-level permissions
        context["form"].instance.owner = self.request.user
        super().cv_form_valid(context)
        for action in ("view", "change", "delete"):
            cv_project.assign_perm(action, self.request.user, self.object)


class ProjectUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, GuardianUpdateViewPermissionRequired):
    cv_viewset = cv_project
    form_class = ProjectForm
    cv_message_template_code = _("Updated project “{{ object }}”")


class ProjectDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, GuardianDeleteViewPermissionRequired):
    cv_viewset = cv_project
    form_class = CrispyDeleteForm
    cv_message_template_code = _("Deleted project “{{ object }}”")
    cv_show_related_objects = True  # cascade preview + labels of the protected tasks the user may view
    cv_modal = True

    def cv_check_delete_protection(self) -> list[str]:
        # a business rule on top of the database's PROTECT: runs on GET (no form shown) and again on POST
        if self.object.is_shared:
            return [gettext("A shared project cannot be deleted. Stop sharing it first.")]
        return []


class TaskTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()
    project = tables.Column()
    owner = tables.Column()


class TaskListView(BreadcrumbMixin, ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_task
    table_class = TaskTable


class TaskDetailView(BreadcrumbMixin, ObjectDetailMixin, GuardianDetailViewPermissionRequired):
    cv_viewset = cv_task
    cv_property_display = [
        {"title": _("Task"), "icon": "fas:list-check", "properties": ["id", "title", "project", "owner"]},
    ]
