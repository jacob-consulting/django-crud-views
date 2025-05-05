from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
from django.views import generic

from .mixins import CrudViewProcessFormMixin


class CreateView(CrudViewProcessFormMixin, CrudView, generic.CreateView):
    template_name = "crud_views/view_create.html"

    cv_key = "create"
    cv_object = False
    cv_path = "create"
    cv_success_key = "list"
    cv_context_actions = crud_views_settings.create_context_actions

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/create.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/create.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/create.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/create.html"

    # icons
    cv_icon_action = "fa-regular fa-square-plus"

    # messages
    cv_message_template: str | None = "crud_views/snippets/message/create.html"

    def cv_form_valid(self, context: dict):
        """
        Handle valid form: save the form instance
        """
        self.object = context["form"].save()


class CreateViewPermissionRequired(CrudViewPermissionRequiredMixin, CreateView):  # this file
    cv_permission = "add"



class CreateViewParentMixin:

    def cv_form_valid(self, context: dict):
        """
        Handle valid form
        """
        assert self.cv_viewset.has_parent, "this ViewSet has no parent"

        parent_object = self.cv_get_parent_object()

        if self.cv_viewset.parent.many_to_many_through_attribute:

            # this saves the object first
            super().cv_form_valid(context)

            # get m2m attribute
            m2m = getattr(parent_object, self.cv_viewset.parent.many_to_many_through_attribute)

            # get through defaults
            through_defaults = self.cv_parent_many_to_many_through_defaults(self.object, parent_object, m2m)

            # add the object to the m2m attribute
            m2m.add(self.object, through_defaults=through_defaults)
        else:
            # before saving, add the parent model to the form instance
            setattr(context["form"].instance, self.cv_get_parent_object_attribute(), parent_object)

            # now save the form
            super().cv_form_valid(context)

    def cv_parent_many_to_many_through_defaults(self, instance, parent_instance, m2m) -> dict:
        return dict()
