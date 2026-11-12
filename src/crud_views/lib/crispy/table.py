"""Numbered column defaults, resolved on a render-local copy."""

from copy import copy
from importlib.metadata import distribution
from pathlib import Path

from crispy_forms.layout import Column
from crispy_forms.utils import TEMPLATE_PACK
from django.template.loader import get_template

from crud_views.lib.button_classes import get_button_class

_BOOTSTRAP5_COLUMN_SOURCE = """<div {% if div.css_id %}id="{{ div.css_id }}"{% endif %}
     class="{% if 'col' in div.css_class %}{{ div.css_class|default:'' }}{% else %}col-md {{ div.css_class|default:'' }}{% endif %}" {{ div.flat_attrs }}>
        {{ fields|safe }}
</div>


"""


def _use_bootstrap5_column_bridge(template_pack, resolved_template) -> bool:
    """Only the installed pack's exact audited source belongs to this bridge."""
    if template_pack != "bootstrap5":
        return False
    origin = resolved_template.origin
    if origin is None or not isinstance(origin.name, str):
        return False
    installed = distribution("crispy-bootstrap5").locate_file(
        "crispy_bootstrap5/templates/bootstrap5/layout/column.html"
    )
    return (
        Path(origin.name).resolve() == Path(installed).resolve()
        and resolved_template.template.source == _BOOTSTRAP5_COLUMN_SOURCE
    )


class _ThemedColumn(Column):
    def __init__(self, *fields, css_class=None, template=None, **kwargs):
        super().__init__(*fields, css_class=css_class, template=template, **kwargs)
        owner = next(cls for cls in type(self).__mro__ if "css_class" in vars(cls))
        self._cv_width = _NUMBERED_COLUMNS.index(owner) + 1 if owner in _NUMBERED_COLUMNS else None
        self._cv_extra_class = css_class
        self._cv_use_registry = self._cv_width is not None
        self._cv_implicit_template = (
            template is None
            and next(cls for cls in type(self).__mro__ if "template" in vars(cls)) is Column
            and type(self).get_template_name is Column.get_template_name
        )

    def __setattr__(self, name, value):
        # Once constructed, direct assignment is authored input, even for an identical value.
        if name == "css_class" and "_cv_use_registry" in self.__dict__:
            self._cv_use_registry = False
        elif name == "template" and "_cv_implicit_template" in self.__dict__:
            self._cv_implicit_template = False
        super().__setattr__(name, value)

    def render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs):
        rendered = copy(self)
        if self._cv_use_registry:
            classes = get_button_class("form", f"column-{self._cv_width}")
            rendered.css_class = " ".join(value for value in (classes, self._cv_extra_class) if value)
        template = get_template(self.get_template_name(template_pack))
        if self._cv_implicit_template and _use_bootstrap5_column_bridge(template_pack, template):
            rendered.template = "crud_views/crispy/bootstrap5_column.html"
        # Div.render supplies its own wrapper mapping and keeps crispy's field bookkeeping local.
        return super(_ThemedColumn, rendered).render(form, context, template_pack, **kwargs)


class Column1(_ThemedColumn):
    css_class = "col-md-1"


class Column2(_ThemedColumn):
    css_class = "col-md-2"


class Column3(_ThemedColumn):
    css_class = "col-md-3"


class Column4(_ThemedColumn):
    css_class = "col-md-4"


class Column5(_ThemedColumn):
    css_class = "col-md-5"


class Column6(_ThemedColumn):
    css_class = "col-md-6"


class Column7(_ThemedColumn):
    css_class = "col-md-7"


class Column8(_ThemedColumn):
    css_class = "col-md-8"


class Column9(_ThemedColumn):
    css_class = "col-md-9"


class Column10(_ThemedColumn):
    css_class = "col-md-10"


class Column11(_ThemedColumn):
    css_class = "col-md-11"


class Column12(_ThemedColumn):
    css_class = "col-md-12"


_NUMBERED_COLUMNS = (
    Column1,
    Column2,
    Column3,
    Column4,
    Column5,
    Column6,
    Column7,
    Column8,
    Column9,
    Column10,
    Column11,
    Column12,
)
