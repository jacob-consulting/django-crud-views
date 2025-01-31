from django.utils.translation import gettext as _
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from crud_views.lib.view import CrudView
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.viewset import path_regs


class RedirectChildView(CrudView, SingleObjectMixin, generic.RedirectView):
    cv_key = "redirect_child"
    cv_path = "child"
    cv_backend_only = True

    # texts and labels
    cv_action_label_template: str = crud_views_settings.child_action_label_template
    cv_action_label_template_code: str = crud_views_settings.child_action_label_template_code
    cv_action_short_label_template: str = crud_views_settings.child_action_short_label_template
    cv_action_short_label_template_code: str = crud_views_settings.child_action_short_label_template_code


    def get_redirect_url(self, *args, **kwargs):
        obj = self.get_object()
        url = self.cv_get_child_url(self.cv_redirect, self.cv_redirect_key, obj)
        return url

    @classmethod
    def cv_get_url_extra_kwargs(cls) -> dict:
        return {"redirect": cls.cv_redirect, "redirect_key": cls.cv_redirect_key}

    @classmethod
    def cv_path_contribute(cls) -> str:
        """
        Contribute path to the path of the view
        """
        pr = path_regs.get_path("redirect", path_regs.KEY)
        pk = path_regs.get_path("redirect_key", path_regs.KEY)
        return f"{pr}/{pk}"
