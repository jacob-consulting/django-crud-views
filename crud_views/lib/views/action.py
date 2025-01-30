from django.http import HttpResponseRedirect
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from crud_views.lib.view import ViewSetView, ViewSetViewPermissionRequiredMixin


class ActionView(ViewSetView, SingleObjectMixin, generic.View):
    cv_list_action_method = "post"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        result = self.action(context)
        # todo: evaluate result
        # todo: message
        url = self.get_success_url()
        return HttpResponseRedirect(url)

    def action(self, context: dict) -> bool:
        raise NotImplementedError("Action not implemented")


class ActionViewPermissionRequired(ViewSetViewPermissionRequiredMixin, ActionView):  # this file
    cv_permission = "change"
