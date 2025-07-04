from django.http import HttpResponseRedirect
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin


class ActionView(CrudView, SingleObjectMixin, generic.View):
    cv_list_action_method = "post"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        result = self.action(context)
        if result:
            self.cv_action_success_hook(context)
        else:
            self.cv_action_error_hook(context)
        # todo: evaluate result
        # todo: message
        url = self.get_success_url()
        return HttpResponseRedirect(url)

    def action(self, context: dict) -> bool:
        raise NotImplementedError("Action not implemented")

    def cv_action_success_hook(self, context: dict) -> None:
        """
        Hook for additional actions after the main action is performed.
        """
        pass

    def cv_action_error_hook(self, context: dict) -> None:
        """
        Hook for additional actions after the main action is performed.
        """
        pass

class ActionViewPermissionRequired(CrudViewPermissionRequiredMixin, ActionView):  # this file
    cv_permission = "change"
