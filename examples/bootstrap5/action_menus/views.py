import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from action_menus.models import Chore, Step
from crud_views.lib.crispy import Column6, Column12, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.view import CardAction, ChildContextButton
from crud_views.lib.views import (
    ActionViewPermissionRequired,
    CardListViewPermissionRequired,
    CreateViewParentMixin,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
    OrderedUpDownPermissionRequired,
    OrderedUpViewPermissionRequired,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ParentViewSet, ViewSet, context_buttons_default
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired

cv_chore = ViewSet(
    model=Chore,
    name="chore",
    icon_header="fa-solid fa-broom",
    context_buttons=[*context_buttons_default(), ChildContextButton(key="steps", child_name="step")],
)

# every action of a chore; which ones stay buttons is decided per location below
CHORE_ACTIONS = ["detail", "update", "done", "archive", "steps", "up", "down", "delete"]


class ChoreForm(CrispyModelForm):
    class Meta:
        model = Chore
        fields = ["title", "done", "archived"]

    def get_layout_fields(self):
        return Row(Column6("title"), Column6("done"))


class ChoreTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()
    done = tables.BooleanColumn()

    class Meta:
        template_name = "action_menus/table_responsive.html"  # scroll container: menus must not clip


class ChoreListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_chore
    table_class = ChoreTable
    cv_list_actions = CHORE_ACTIONS
    cv_list_actions_inline = ["detail", "up", "down"]  # the rest folds into the ⋯ menu
    cv_context_actions = ["card", "create"]


class ChoreCardListView(BreadcrumbMixin, CardListViewPermissionRequired):
    cv_viewset = cv_chore
    cv_context_actions = ["home", "create"]
    cv_card_actions = [
        CardAction(key="detail", label=_("Details"), variant="primary", flex=True),
        CardAction(key="update", label=_("Edit")),
        CardAction(key="done", label=_("Done")),
        CardAction(key="archive", label=_("Archive")),
        CardAction(child_name="step", label=_("Steps")),
        CardAction(key="delete", label=_("Delete")),
    ]
    cv_card_actions_inline = ["detail"]


class ChoreDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_chore
    cv_context_actions = ["home", "detail", "update", "done", "archive", "steps", "delete"]
    cv_context_actions_inline = ["update"]  # the active "detail" shows inside the menu
    cv_property_display = [
        {"title": _("Chore"), "icon": "broom", "properties": ["title", "done", "archived"]},
    ]


class ChoreCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_chore
    form_class = ChoreForm
    cv_message_template_code = _("Created chore “{{ object }}”")


class ChoreUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_chore
    form_class = ChoreForm
    cv_context_actions = ["home", "detail", "update", "delete"]
    cv_context_actions_inline = ["update"]  # the active "update" stays an inline button
    cv_message_template_code = _("Updated chore “{{ object }}”")


class ChoreDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_chore
    form_class = CrispyDeleteForm
    cv_modal = True  # opens in a modal, also from inside the menu
    cv_message_template_code = _("Deleted chore “{{ object }}”")


class ChoreDoneView(BreadcrumbMixin, MessageMixin, ActionViewPermissionRequired):
    cv_viewset = cv_chore
    cv_key = "done"
    cv_path = "done"
    cv_permission = "change"
    cv_backend_only = True
    cv_icon_action = "fa-solid fa-check"
    cv_action_label_template_code = _("Toggle done")
    cv_action_short_label_template_code = _("Done")
    cv_message_template_code = _("Toggled done for “{{ object }}”")
    cv_message_template_error_code = _("Could not toggle done for “{{ object }}”")

    def action(self, context) -> bool:
        self.object.done = not self.object.done
        self.object.save()
        return True


class ChoreArchiveView(BreadcrumbMixin, MessageMixin, ActionViewPermissionRequired):
    cv_viewset = cv_chore
    cv_key = "archive"
    cv_path = "archive"
    cv_permission = "change"
    cv_backend_only = True
    cv_inaccessible_actions = "disable"  # bob sees this one greyed out instead of hidden
    cv_icon_action = "fa-solid fa-box-archive"
    cv_action_label_template_code = _("Archive")
    cv_action_short_label_template_code = _("Archive")
    cv_message_template_code = _("Toggled archive for “{{ object }}”")
    cv_message_template_error_code = _("Could not archive “{{ object }}”")

    def action(self, context) -> bool:
        self.object.archived = not self.object.archived
        self.object.save()
        return True


class ChoreUpView(BreadcrumbMixin, MessageMixin, OrderedUpViewPermissionRequired):
    cv_viewset = cv_chore
    cv_message_template_code = _("Moved chore “{{ object }}” up")


class ChoreDownView(BreadcrumbMixin, MessageMixin, OrderedUpDownPermissionRequired):
    cv_viewset = cv_chore
    cv_message_template_code = _("Moved chore “{{ object }}” down")


cv_step = ViewSet(model=Step, name="step", icon_header="fa-solid fa-list-check", parent=ParentViewSet(name="chore"))


class StepForm(CrispyModelForm):
    class Meta:
        model = Step
        fields = ["text"]

    def get_layout_fields(self):
        return Row(Column12("text"))


class StepTable(Table):
    text = tables.Column()


class StepListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_step
    table_class = StepTable
    cv_list_actions = ["update", "delete"]


class StepCreateView(
    BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_step
    form_class = StepForm
    cv_message_template_code = _("Created step “{{ object }}”")


class StepUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_step
    form_class = StepForm
    cv_message_template_code = _("Updated step “{{ object }}”")


class StepDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_step
    form_class = CrispyDeleteForm
    cv_message_template_code = _("Deleted step “{{ object }}”")
