"""Opt-in current-page selection and permission-gated action forms."""

from dataclasses import dataclass
from functools import partial
from typing import ClassVar

import django_tables2 as tables
from django.contrib import messages
from django.core.exceptions import BadRequest, ImproperlyConfigured, ValidationError
from django.db import DEFAULT_DB_ALIAS, DataError, router, transaction
from django.db.models import QuerySet, Subquery
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from crud_views.lib.ancestors import _scope_child_queryset
from crud_views.lib.crispy import CrispyForm, CrispyViewMixin
from crud_views.lib.crispy.buttons import FORM_LEAF_TEMPLATE
from crud_views.lib.view.button_data import cv_button_data
from crud_views.lib.views.form import CustomFormNoObjectViewPermissionRequired
from crud_views.lib.views.mixins import MessageMixin

__all__ = ["BulkConfirmForm", "BulkFormViewPermissionRequired", "BulkSelectionMixin"]


class BulkSelectionMixin:
    """Add selection controls only; never process a POST.

    Place this mixin before ListViewTableMixin, whose get_table_kwargs does not call super().
    """

    cv_bulk_actions: ClassVar[tuple[str, ...]] = ()
    cv_bulk_form_id = "cv-bulk-selection"

    @property
    def cv_bulk_buttons(self):
        context = self.cv_get_view_context()
        buttons = []
        for key in self.cv_bulk_actions:
            destination = self.cv_viewset.get_view_class(key)
            raw = {
                "cv_key": "submit",
                "cv_type": "submit",
                "cv_name": "cv_bulk_stage",
                "cv_value": "review",
                "cv_label": destination.cv_get_action_short_label(context),
                "cv_id": f"cv-bulk-{key}",
                "cv_icon": destination.cv_icon_action,
                "cv_attrs": {"formaction": self.cv_get_link_url(destination, key), "data-cv-bulk-action": key},
            }
            buttons.append(render_to_string(FORM_LEAF_TEMPLATE, cv_button_data(raw, "form")))
        return buttons

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs()
        if not self.cv_bulk_actions:
            return kwargs
        table_class = self.get_table_class()
        sequence = kwargs.get("sequence") or table_class._meta.sequence
        if not sequence:
            sequence = ("...", "actions") if "actions" in table_class.base_columns else ("...",)
        column = tables.TemplateColumn(
            template_name="crud_views/columns/bulk_select.html", verbose_name=_("Select"), orderable=False
        )
        kwargs["extra_columns"] = [("cv_bulk_select", column), *kwargs.get("extra_columns", ())]
        kwargs["sequence"] = ("cv_bulk_select", *(name for name in sequence if name != "cv_bulk_select"))
        return kwargs


class BulkConfirmForm(CrispyForm):
    """A fieldless action form with the themed Confirm and Cancel buttons."""

    submit_label = gettext_lazy("Confirm")

    def get_layout_fields(self):
        return []


@dataclass(frozen=True)
class _BlockedItem:
    pk: str
    label: str | None
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class _Review:
    objects: tuple
    blocked: tuple[_BlockedItem, ...]

    @property
    def ids(self):
        return tuple(str(obj.pk) for obj in self.objects)


def _read_ids(post, field):
    """Normalize both bounded transport lists without losing their submitted order."""

    def canonical(values):
        try:
            if any(not isinstance(value, str) or not value or "\x00" in value for value in values):
                raise ValueError
            return tuple(dict.fromkeys(str(field.to_python(value)) for value in values))
        except (ValidationError, ValueError, TypeError, OverflowError) as error:
            raise BadRequest("Invalid selected object IDs.") from error

    candidates = canonical(post.getlist("cv_bulk_ids"))
    excluded = canonical(post.getlist("cv_bulk_blocked_ids"))
    if set(candidates) & set(excluded):
        raise BadRequest("An object cannot be both selected and excluded.")
    return candidates, excluded


class BulkFormViewPermissionRequired(MessageMixin, CrispyViewMixin, CustomFormNoObjectViewPermissionRequired):
    """Review and execute selected objects inside the destination's own permission and scope.

    cv_bulk_objects is set by the view per request and is not configured by a subclass.
    """

    cv_object = False
    cv_permission = None
    cv_modal_supported = False
    cv_bulk_max = 100
    cv_bulk_confirm = True
    cv_bulk_objects = ()
    form_class = BulkConfirmForm
    template_name = "crud_views/view_bulk_form.html"
    cv_content_template = "crud_views/view_bulk_form.content.html"
    cv_paragraph_template = "crud_views/snippets/paragraph/bulk.html"
    cv_message_template = "crud_views/snippets/message/bulk.html"
    cv_context_actions: ClassVar[list[str]] = ["home"]
    cv_header_template_code = "{{ view.cv_bulk_header }}"
    _cv_ancestor_operation = "write"
    _bulk_stage = "review"

    @property
    def cv_bulk_header(self):
        return self.cv_get_action_label(self.cv_get_view_context())

    def cv_bulk_has_permission(self, obj):
        return True

    def cv_bulk_check(self, obj):
        return []

    def _selection_queryset(self):
        base = self.cv_viewset.get_queryset(view=self)
        visible = self.get_queryset()
        for queryset in (base, visible):
            if (
                not isinstance(queryset, QuerySet)
                or queryset.model is not self.cv_viewset.model
                or queryset.query.is_sliced
                or queryset.db != DEFAULT_DB_ALIAS
            ):
                raise ImproperlyConfigured(
                    "Bulk selection requires unsliced querysets for the ViewSet model on the default database."
                )
        base = _scope_child_queryset(self, base)
        return visible.filter(pk__in=Subquery(base.order_by().values("pk")))

    def _review_selection(self, candidates, excluded):
        if self.cv_get_db_alias() != DEFAULT_DB_ALIAS:
            raise ImproperlyConfigured("This bulk form supports the default database only.")
        ids = (*candidates, *excluded)
        queryset = self._selection_queryset().filter(pk__in=ids).order_by()
        try:
            objects = {str(obj.pk): obj for obj in queryset}
        except (OverflowError, DataError) as error:
            raise BadRequest("Invalid selected object IDs.") from error
        eligible, blocked = [], []
        excluded_set = set(excluded)
        unavailable_reason = (_("This item is unavailable for this action."),)
        for pk in ids:
            obj = objects.get(pk)
            if obj is None:
                blocked.append(_BlockedItem(pk, None, unavailable_reason))
                continue
            if obj._state.db != DEFAULT_DB_ALIAS or router.db_for_write(type(obj), instance=obj) != DEFAULT_DB_ALIAS:
                raise ImproperlyConfigured("Bulk objects must use the default write database.")
            if not self.cv_bulk_has_permission(obj):
                blocked.append(_BlockedItem(pk, None, unavailable_reason))
                continue
            reasons = tuple(self.cv_bulk_check(obj))
            if reasons or pk in excluded_set:
                blocked.append(
                    _BlockedItem(
                        pk,
                        str(obj),
                        reasons or (_("Excluded from this confirmation; select it again from the list."),),
                    )
                )
            else:
                eligible.append(obj)
        return _Review(tuple(eligible), tuple(blocked))

    def _bulk_back_url(self):
        """Deliberately fall back to success when no cancel target is accessible (D-34).

        Both URLs are built by reverse(), never from request data.
        """
        return self.cv_get_cancel_url() or self.get_success_url()

    def _bulk_back(self, message):
        messages.warning(self.request, message)
        return HttpResponseRedirect(self._bulk_back_url())

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(self._bulk_back_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self._bulk_stage == "review":
            kwargs.pop("data", None)
            kwargs.pop("files", None)
        return kwargs

    def _bulk_context(self, review):
        return self.get_context_data(form=self.get_form(), bulk_review=review)

    def post(self, request, *args, **kwargs):
        self.object = None
        if request.POST.getlist("cv_bulk_stage") not in (["review"], ["execute"]):
            raise BadRequest("Invalid bulk stage.")
        count = len(request.POST.getlist("cv_bulk_ids")) + len(request.POST.getlist("cv_bulk_blocked_ids"))
        if count == 0:
            return self._bulk_back(_("Select at least one record."))
        if count > self.cv_bulk_max:
            return self._bulk_back(_("Select at most %(max)d records.") % {"max": self.cv_bulk_max})
        candidates, excluded = _read_ids(request.POST, self.cv_viewset.model._meta.pk)
        self._bulk_stage = request.POST["cv_bulk_stage"]
        if self._bulk_stage == "review":
            review = self._review_selection(candidates, excluded)
            self.cv_bulk_objects = review.objects
            return self.render_to_response(self._bulk_context(review))
        return self._bulk_execute(candidates, excluded)

    def _bulk_execute(self, candidates, excluded):
        """An override of cv_form_valid_process does not run on a bulk destination.

        Applications override cv_form_valid (the write) or cv_form_valid_hook, inside the transaction
        that also contains this request's eligibility check.
        """
        self._cv_check_nested_write()
        with self.cv_get_atomic():
            review = self._review_selection(candidates, excluded)
            self.cv_bulk_objects = review.objects
            unchanged = bool(review.objects) and review.ids == candidates
            context = self._bulk_context(review)
            self._cv_check_nested_write(context)
            self.cv_post_hook(context)
            valid = self.cv_form_is_valid(context)
            if not unchanged:
                context["form"].add_error(None, _("The eligible selection changed. Review it and confirm again."))
                valid = False
            if not valid:
                self.cv_form_invalid_hook(context)
                return self.cv_form_invalid(context)
            self.cv_form_valid(context)
            self.cv_form_valid_hook(context)
            transaction.on_commit(partial(self.cv_on_commit, context), using=self.cv_get_db_alias())
        return self.cv_form_valid_redirect(context)
