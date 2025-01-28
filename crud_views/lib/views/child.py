from django.utils.translation import gettext as _
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from crud_views.lib.view import ViewSetView
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.viewset import path_regs


class RedirectChildView(ViewSetView, SingleObjectMixin, generic.RedirectView):
    vs_key = "redirect_child"
    vs_path = "child"
    vs_backend_only = True

    # texts and labels
    vs_action_label_template: str = crud_views_settings.child_action_label_template
    vs_action_label_template_code: str = crud_views_settings.child_action_label_template_code
    vs_action_short_label_template: str = crud_views_settings.child_action_short_label_template
    vs_action_short_label_template_code: str = crud_views_settings.child_action_short_label_template_code


    def get_redirect_url(self, *args, **kwargs):
        obj = self.get_object()
        url = self.vs_get_child_url(self.vs_redirect, self.vs_redirect_key, obj)
        return url

    @classmethod
    def vs_get_url_extra_kwargs(cls) -> dict:
        return {"redirect": cls.vs_redirect, "redirect_key": cls.vs_redirect_key}

    @classmethod
    def vs_path_contribute(cls) -> str:
        """
        Contribute path to the path of the view
        """
        pr = path_regs.get_path("redirect", path_regs.KEY)
        pk = path_regs.get_path("redirect_key", path_regs.KEY)
        return f"{pr}/{pk}"
