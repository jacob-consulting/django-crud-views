"""Explicit compact columns and request-local crispy presentation."""

from dataclasses import KW_ONLY, dataclass

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Row
from django.core.exceptions import ImproperlyConfigured
from django.forms import widgets

from .layout import FormControl


def _validate_span(value, name):
    if type(value) is not int or not 1 <= value <= 12:
        raise ValueError(f"{name} must be an integer from 1 to 12")


@dataclass(frozen=True)
class CompactColumn:
    field: str
    _: KW_ONLY
    span: int

    def __post_init__(self):
        if not isinstance(self.field, str) or not self.field or any(char.isspace() for char in self.field):
            raise ValueError("CompactColumn.field must be a nonempty exact field name without whitespace")
        _validate_span(self.span, "CompactColumn.span")


@dataclass(frozen=True)
class CompactLayout:
    columns: tuple[CompactColumn, ...]
    _: KW_ONLY
    controls_span: int

    def __post_init__(self):
        if not isinstance(self.columns, (list, tuple)) or not self.columns:
            raise ValueError("CompactLayout.columns must be a nonempty list or tuple of CompactColumn instances")
        if any(not isinstance(column, CompactColumn) for column in self.columns):
            raise ValueError("CompactLayout.columns must contain CompactColumn instances")
        object.__setattr__(self, "columns", tuple(self.columns))
        names = [column.field for column in self.columns]
        if len(set(names)) != len(names):
            raise ValueError("CompactLayout.columns must not contain duplicate field names")
        _validate_span(self.controls_span, "CompactLayout.controls_span")
        if sum(column.span for column in self.columns) + self.controls_span > 12:
            raise ValueError("CompactLayout field and controls spans must total at most 12")


@dataclass(frozen=True)
class _CompactHeading:
    field: str
    span: int
    label: str
    required: bool


def _compact_schema(form, declaration):
    """Read field metadata without rendering widgets or evaluating choices."""
    layout = declaration.compact_layout
    roles = {declaration.klass.model._meta.pk.name, declaration.klass.fk.name, "ORDER", "DELETE"}
    columns = {column.field for column in layout.columns}

    def invalid(name, reason):
        raise ImproperlyConfigured(f"FormSet '{declaration.key}' compact field '{name}': {reason}")

    for name, field in form.fields.items():
        if name not in roles and not field.widget.is_hidden and name not in columns:
            invalid(name, "visible field is missing from CompactLayout")
    headings = []
    supported = (widgets.TextInput, widgets.NumberInput, widgets.DateInput, widgets.Select)
    for column in layout.columns:
        name = column.field
        if name not in form.fields:
            invalid(name, "field does not exist")
        field = form.fields[name]
        if name in roles or field.widget.is_hidden:
            invalid(name, "hidden and identity/control fields cannot be compact columns")
        widget = field.widget
        if type(widget) not in supported or widget.template_name != type(widget).template_name:
            invalid(name, "unsupported compact widget or custom template")
        label = form[name].label
        if label is None or not str(label).strip():
            invalid(name, "a nonempty effective label is required")
        headings.append(_CompactHeading(name, column.span, str(label), field.required))
    return tuple(headings)


def _compact_projection(x_formset):
    declaration = x_formset.formset
    if declaration.compact_layout is None:
        return ()
    if not x_formset.forms:
        raise ImproperlyConfigured(f"FormSet '{x_formset.key}': compact metadata requires a form")
    columns = _compact_schema(x_formset.forms[0].form, declaration)
    for row in x_formset.forms[1:]:
        if _compact_schema(row.form, declaration) != columns:
            raise ImproperlyConfigured(f"FormSet '{x_formset.key}': compact rows must have uniform fields and labels")
    return columns


def _compact_helper(x_form):
    declaration = x_form.parent.formset
    columns = x_form.parent.compact_columns  # Validate all rows before crispy can mutate hidden widgets.
    helper = FormHelper()
    helper.form_tag = False
    helper.disable_csrf = True
    helper.render_hidden_fields = True
    helper.form_show_labels = True
    helper.label_class = "cv-formset-compact-label"
    cells = [Div(column.field, css_class=f"col-md-{column.span}") for column in columns]
    cells.append(Div(FormControl(formset=declaration), css_class=f"col-md-{declaration.compact_layout.controls_span}"))
    hidden = [Field(name, type="hidden") for name in ("ORDER", "DELETE") if name in x_form.form.fields]
    helper.layout = Layout(Row(*cells, css_class="cv-formset-compact-fields"), *hidden)
    return helper
