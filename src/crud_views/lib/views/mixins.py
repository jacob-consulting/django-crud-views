import json
from typing import Iterable
from urllib.parse import parse_qs, urlencode

from django.contrib import messages
from django.core.exceptions import BadRequest
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from crud_views.lib.check import Check, CheckTemplateOrCode
from crud_views.lib.session import SessionData
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view.base import cv_is_modal_request


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

        # views with object context (update, object-based custom forms) resolve their
        # object; create and no-object views run with object=None
        self.object = self.get_object() if self.cv_object else None  # noqa

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
        Handle invalid form; modal requests are answered with 422 so the client
        can distinguish the re-rendered partial from a confirmation page.
        """
        response = self.render_to_response(context)
        if self.cv_modal and cv_is_modal_request(self.request):
            response.status_code = 422
        return response

    def cv_form_invalid_hook(self, context: dict):
        """
        Handle invalid form hook
        """
        pass

    def cv_form_valid_redirect(self, context: dict) -> HttpResponse:
        """
        Redirect to the success url.
        Modal requests get 204 + X-CV-Redirect instead of a 302: fetch() follows
        redirects transparently, so the client needs the target as data.
        """
        url = self.get_success_url()
        if self.cv_modal and cv_is_modal_request(self.request):
            response = HttpResponse(status=204)
            response["X-CV-Redirect"] = url
            return response
        return HttpResponseRedirect(url)

    def cv_form_invalid_redirect(self, context: dict) -> HttpResponseRedirect:
        """
        Handle invalid form
        """
        return self.render_to_response(context)


class MessageMixin:
    """
    Add messages for a view.
    Note: the view must configure the message template or code:
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

    def cv_form_valid_hook(self, context: dict):
        super().cv_form_valid_hook(context)  # noqa
        message = self.cv_get_message()
        if message:
            messages.success(self.request, message)


class CardOrderMixin:
    """
    Adds order-by + direction support to card views.

    The order field is whitelisted against ``cv_order_fields`` so an arbitrary
    GET parameter can never reach ``QuerySet.order_by()`` (no ordering injection).
    Direction is restricted to ``asc`` / ``desc``.
    """

    cv_order_fields: list = []  # list[str | tuple[str, str]]: field name or (name, label)
    cv_order_default: str | None = None  # e.g. "-name"; leading "-" => descending
    cv_order_param: str = "order"
    cv_order_dir_param: str = "dir"

    def cv_get_order_field_names(self) -> list[str]:
        return [f[0] if isinstance(f, (tuple, list)) else f for f in self.cv_order_fields]

    def cv_get_order(self) -> tuple[str | None, str]:
        """Resolve (field_name_or_None, direction) from GET, whitelisted."""
        names = self.cv_get_order_field_names()
        field = self.request.GET.get(self.cv_order_param) or ""
        direction = self.request.GET.get(self.cv_order_dir_param) or "asc"
        if direction not in ("asc", "desc"):
            direction = "asc"
        if field in names:
            return field, direction
        # not selected / not whitelisted -> fall back to default ordering
        if self.cv_order_default:
            default = self.cv_order_default
            if default.startswith("-"):
                return default[1:], "desc"
            return default, "asc"
        return None, direction

    def get_queryset(self):
        qs = super().get_queryset()
        field, direction = self.cv_get_order()
        if field:
            prefix = "-" if direction == "desc" else ""
            qs = qs.order_by(f"{prefix}{field}")
        return qs

    def cv_get_order_choices(self) -> list[dict]:
        current, _ = self.cv_get_order()
        choices = []
        for f in self.cv_order_fields:
            if isinstance(f, (tuple, list)):
                name, label = f[0], f[1]
            else:
                name = f
                try:
                    label = str(self.model._meta.get_field(name).verbose_name).capitalize()
                except Exception:  # pragma: no cover - defensive
                    label = name
            choices.append({"name": name, "label": label, "selected": name == current})
        return choices

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current, direction = self.cv_get_order()
        context["cv_order_choices"] = self.cv_get_order_choices()
        context["cv_order_current"] = current or ""
        context["cv_order_dir"] = direction
        context["cv_order_param"] = self.cv_order_param
        context["cv_order_dir_param"] = self.cv_order_dir_param
        # all current GET params except order/dir/page, for the toolbar's hidden inputs
        preserved = []
        skip = {self.cv_order_param, self.cv_order_dir_param, "page"}
        for key in self.request.GET:
            if key in skip:
                continue
            for value in self.request.GET.getlist(key):
                preserved.append({"name": key, "value": value})
        context["cv_order_preserved_params"] = preserved
        return context


class ListViewTableMixin(SingleTableMixin):
    """
    Mixin for ListView to render tables with django-tables2
    """

    template_name = "crud_views/view_list_table.html"
    cv_content_template = "crud_views/view_list_table.content.html"

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
    cv_filter_pinned: bool = crud_views_settings.filter_pinned

    def get_filterset(self, filterset_class):  # noqa
        kwargs = self.get_filterset_kwargs(filterset_class)
        filterset = filterset_class(**kwargs)
        if self.formhelper_class:
            filterset.form.helper = self.formhelper_class(request=self.request, view=self)
        return filterset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.cv_filter_pinned:
            # pinned filter is always shown; the toggle/session-expanded state is moot
            filter_expanded = True
        else:
            filter_expanded = SessionData.from_view(self).get("filter_expanded", False)
        context["cv_filter_pinned"] = self.cv_filter_pinned
        context["cv_filter_expanded"] = filter_expanded
        return context

    def post(self, request, *args, **kwargs):
        """
        Store filter expanded state
        """

        if not self.cv_filter_persistence:
            return JsonResponse({"status": "ok", "filter_expanded": None})

        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise BadRequest("invalid JSON body")
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
            query_string = self.request.META["QUERY_STRING"]

            # reset filter ?
            qs = parse_qs(query_string)
            reset_filter = qs.get("reset_filter", ["false"])[0] == "true"
            if reset_filter:
                try:
                    del sd[self.cv_session_key_querystring]
                except KeyError:
                    pass
                url = self.request.path
                keep = {}
                order_param = getattr(self, "cv_order_param", "order")
                dir_param = getattr(self, "cv_order_dir_param", "dir")
                for key in ("sort", order_param, dir_param):
                    value = qs.get(key, [None])[0]
                    if value:
                        keep[key] = value
                if keep:
                    url += "?" + urlencode(keep)
                return HttpResponseRedirect(url)

            # there is a query string, update data
            if len(query_string) > 0:
                sd[self.cv_session_key_querystring] = query_string

            # no query string, but data in session, restore query string
            if len(query_string) == 0 and len(stored_query_string):
                redirect_to = self.request.path + "?" + stored_query_string
                return HttpResponseRedirect(redirect_to)

        return super().get(request, *args, **kwargs)
