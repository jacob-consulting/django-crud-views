import json
from typing import Iterable
from urllib.parse import parse_qs

from django.contrib import messages
from django.core.exceptions import BadRequest
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from crud_views.lib.check import Check, CheckTemplateOrCode
from crud_views.lib.session import SessionData
from crud_views.lib.settings import crud_views_settings


class CrudViewProcessFormMixin:
    """
    Mixin for create and update views.
    Note ProcessFormView.post is overridden.
    Why? Because we need a more detailed handling of the post method.
    """

    def post(self, request, *args, **kwargs):
        """
        Override ProcessFormView
        """

        try:
            self.object = self.get_object()  # noqa
        except AttributeError:
            self.object = None  # noqa

        context = self.get_context_data(**kwargs)
        self.cv_post_hook(context)
        if self.cv_form_is_valid(context):
            self.cv_form_valid(context)
            self.cv_form_valid_hook(context)
            return self.cv_form_valid_redirect(context)
        else:
            self.cv_form_invalid_hook(context)
            return self.cv_form_invalid(context)

    def cv_post_hook(self, context: dict):
        """
        Hook on post.
        Crud Views modules may extend this method.
        """
        pass

    def cv_form_is_valid(self, context: dict) -> bool:
        """
        Check if the form is valid.
        Crud Views modules may extend this method with further checks.
        """
        return context["form"].is_valid()

    def cv_form_valid(self, context: dict):
        """
        Handle valid form
        """
        pass

    def cv_form_valid_hook(self, context: dict):
        """
        Handle valid form hook
        """
        pass

    def cv_form_invalid(self, context: dict):
        """
        Handle invalid form
        """
        return self.render_to_response(context)

    def cv_form_invalid_hook(self, context: dict):
        """
        Handle invalid form hook
        """
        pass

    def cv_form_valid_redirect(self, context: dict) -> HttpResponseRedirect:
        """
        Redirect to the success url
        """
        return HttpResponseRedirect(self.get_success_url())

    def cv_form_invalid_redirect(self, context: dict) -> HttpResponseRedirect:
        """
        Handle invalid form
        """
        return self.render_to_response(context)


class MessageMixin:
    """
    Add messages for a view.
    Note: the view must configure the message template and message template or code:
            - cv_message_template
            - cv_message_template_code
    """

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield from super().checks()  # noqa
        yield CheckTemplateOrCode(context=cls, attribute="cv_message_template")

    def cv_get_message(self, attribute: str = "cv_message") -> str | None:
        return self.render_snippet(self.cv_get_meta(),
                                   self.cv_message_template,
                                   self.cv_message_template_code, )

    def cv_form_valid_hook(self, context: dict):
        message = self.cv_get_message()
        if message:
            messages.success(self.request, message)

    def action(self, context: dict) -> bool:
        result = super().action(context)
        if result:
            messages.success(self.request, self.cv_get_message())
        elif hasattr(self, "cv_error_message"):
            # error message is optional
            messages.error(self.request, self.cv_get_message("cv_error_message"))

        return result


class ListViewTableMixin(SingleTableMixin):
    """
    Mixin for ListView to render tables with django-tables2
    """
    template_name = "crud_views/view_list_table.html"

    table: SingleTableMixin = None
    table_class: str = None
    paginate_by: int = 10

    def get_table_kwargs(self):
        return {"view": self}


class ListViewTableFilterMixin(FilterView):
    """
    Mixin for ListView to add a filter with django-filter.
    Additionally, there is a filter persistence for the fields and the expanded state of the filter.
    Persistence ist store in the user session.

    Note: not all themes may support the expanded state of the filter.
    """

    filterset_class = None
    formhelper_class = None

    cv_filter_persistence: bool = crud_views_settings.filter_persistence
    cv_session_key_querystring: str = "filter_query_string"

    # todo: check cv_filter_persistence cv_session_key_querystring

    def get_filterset(self, filterset_class):  # noqa
        kwargs = self.get_filterset_kwargs(filterset_class)
        filterset = filterset_class(**kwargs)
        if self.formhelper_class:
            filterset.form.helper = self.formhelper_class(request=self.request)
        return filterset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        filter_expanded = SessionData.from_view(self).get("filter_expanded", False)
        #
        # with SessionData.from_view(self) as sd:
        #     filter_expanded = sd["filter_expanded"]

        context["cv_filter_expanded"] = filter_expanded
        return context

    def post(self, request, *args, **kwargs):
        """
        Store filter expanded state
        """

        if not self.cv_filter_persistence:
            return JsonResponse({"status": "ok", "filter_expanded": None})

        data = json.loads(request.body.decode("utf-8"))
        filter_expanded = data.get("filter_expanded", None)
        if filter_expanded is None:
            raise BadRequest("filter_expanded not set")

        with SessionData.from_view(self) as sd:
            sd["filter_expanded"] = filter_expanded

        return JsonResponse({"status": "ok", "filter_expanded": filter_expanded})

    def get(self, request, *args, **kwargs):
        """
        Add filter persistence via session here.
        This was inspired by Lorenzo Prodon's django-persistent-filters:
            https://github.com/LorenzoProd/django-persistent-filters
        """

        if not self.cv_filter_persistence:
            return super().get(request, *args, **kwargs)

        with SessionData.from_view(self) as sd:

            # get stored query string and request query string
            stored_query_string = sd.get(self.cv_session_key_querystring, "")
            query_string = self.request.META['QUERY_STRING']

            # reset filter ?
            qs = parse_qs(query_string)  # todo: is this correct? looks strange with that lists
            reset_filter = qs.get("reset_filter", ["false"])[0] == "true"
            if reset_filter:
                try:
                    del sd[self.cv_session_key_querystring]
                except KeyError:
                    pass
                url = self.request.path
                sort = qs.get("sort", [None])[0]
                if sort:
                    url += f"?sort={sort}"
                return HttpResponseRedirect(url)

            # there is a query string, update data
            if len(query_string) > 0:
                sd[self.cv_session_key_querystring] = query_string

            # no query string, but data in session, restore query string
            if len(query_string) == 0 and len(stored_query_string):
                redirect_to = self.request.path + '?' + stored_query_string
                return HttpResponseRedirect(redirect_to)

        return super().get(request, *args, **kwargs)
