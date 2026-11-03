"""Private library action groups; pack templates retain ownership of their wrappers."""

from copy import copy
from importlib.metadata import distribution
from pathlib import Path

from crispy_forms.bootstrap import FormActions
from crispy_forms.utils import TEMPLATE_PACK
from django.template.loader import get_template

from crud_views.lib.button_classes import get_button_class

_BOOTSTRAP5_FLOOR_SOURCE = """<div{% if formactions.attrs %} {{ formactions.flat_attrs }}{% endif %} class="mb-3">
    {% if label_class %}
        <div class="aab {{ label_class }}"></div>
    {% endif %}

    <div class="{{ field_class }}">
        {{ fields_output|safe }}
    </div>
</div>
"""


def _use_bootstrap5_floor_bridge(template_pack, resolved_template) -> bool:
    """Only the installed pack's exact audited 2023.10 source can use this bridge."""
    if template_pack != "bootstrap5":
        return False
    origin = resolved_template.origin
    if origin is None or not isinstance(origin.name, str):
        return False
    installed = distribution("crispy-bootstrap5").locate_file(
        "crispy_bootstrap5/templates/bootstrap5/layout/formactions.html"
    )
    return (
        Path(origin.name).resolve() == Path(installed).resolve()
        and resolved_template.template.source == _BOOTSTRAP5_FLOOR_SOURCE
    )


class _ThemedFormActions(FormActions):
    """Resolve the utility per render without changing authored classes or cached helper layouts."""

    def __init__(self, *fields, class_key="form:actions", **kwargs):
        self._cv_class_key = class_key
        super().__init__(*fields, **kwargs)

    def render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs):
        rendered = copy(self)
        location, slot = self._cv_class_key.split(":", 1)
        extra = get_button_class(location, slot)
        rendered.css_class = " ".join(value for value in (self.css_class, extra) if value)
        template = get_template(self.get_template_name(template_pack))
        if _use_bootstrap5_floor_bridge(template_pack, template):
            template = get_template("crud_views/crispy/bootstrap5_formactions.html")
        fields = self.get_rendered_fields(form, context, template_pack, **kwargs)
        context.update({"formactions": rendered, "fields_output": fields})
        return template.render(context.flatten())
