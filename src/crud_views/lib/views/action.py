from functools import partial

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin


class ActionView(CrudView, SingleObjectMixin, generic.View):
    cv_list_action_method = "post"
    cv_action_messages: bool = True  # set False to suppress success/error messages

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        self.cv_action_process(context)
        url = self.get_success_url()
        return HttpResponseRedirect(url)

    def cv_action_process(self, context: dict) -> bool:
        """
        Write phase of the action: action() and the success/error message + hook run inside
        cv_get_atomic(); on success cv_on_commit is scheduled to run after the commit.
        A falsy result does NOT roll back; call transaction.set_rollback(True) in action() for that.
        """
        with self.cv_get_atomic():
            result = self.action(context)
            if result:
                self.cv_action_success(context)
                transaction.on_commit(partial(self.cv_on_commit, context), using=self.cv_get_db_alias())
            else:
                self.cv_action_error(context)
        return result

    def action(self, context: dict) -> bool:
        raise NotImplementedError("Action not implemented")

    def cv_action_success(self, context: dict) -> None:
        if self.cv_action_messages:
            message = self.cv_get_message()
            if message:
                messages.success(self.request, message)
        self.cv_action_success_hook(context)

    def cv_action_error(self, context: dict) -> None:
        if self.cv_action_messages:
            message = self.cv_get_message(error=True)
            if message:
                messages.error(self.request, message)
        self.cv_action_error_hook(context)

    def cv_action_success_hook(self, context: dict) -> None:
        """Hook for additional side effects after a successful action."""
        pass

    def cv_action_error_hook(self, context: dict) -> None:
        """Hook for additional side effects after a failed action."""
        pass


class ActionViewPermissionRequired(CrudViewPermissionRequiredMixin, ActionView):  # this file
    cv_permission = "change"
