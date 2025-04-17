import django_tables2 as tables
from django_tables2 import Column

from crud_views.lib.exceptions import ViewSetKeyFoundError, ignore_exception
from crud_views.lib.table.attrs import ColAttr, ColumnAttrs

from crud_views.lib.viewset import ViewSet


class ViewAwareColumnMixin:
    pass


class ActionColumn(tables.TemplateColumn):

    def __init__(self, **extra):
        if "orderable" not in extra:
            extra["orderable"] = False
        if "template_name" not in extra:
            extra["template_name"] = "crud_views/columns/actions.html"
        if "attrs" not in extra:
            extra["attrs"] = ColAttr.action
        super().__init__(**extra)

    def render(self, record, table, value, bound_column, **kwargs):
        self.extra_context["view"] = table.view
        return super().render(record, table, value, bound_column, **kwargs)


class LinkChildColumn(tables.TemplateColumn):

    def __init__(self, name: str, key: str = "list", **extra):
        self.name = name
        self.key = key
        if "orderable" not in extra:
            extra["orderable"] = False
        if "template_code" not in extra and "template_name" not in extra:
            extra["template_name"] = "crud_views/columns/child.html"
        super().__init__(**extra)

    def render(self, record, table, value, bound_column, **kwargs):

        viewset = ViewSet.get_viewset(self.name)
        data = viewset.get_meta(table.view.cv_get_view_context())
        data.update({
            "url": table.view.cv_get_child_url(self.name, self.key, record)
        })
        self.extra_context.update(data)
        return super().render(record, table, value, bound_column, **kwargs)


class LinkDetailColumnMixin:
    @ignore_exception(ViewSetKeyFoundError)
    def get_url(self, table, record, **kwargs):
        return table.view.cv_get_url("detail", obj=record)


class LinkDetailColumn(LinkDetailColumnMixin, Column):
    pass


class UUIDColumn(tables.TemplateColumn):

    def __init__(self, template_name="crud_views/columns/uuid.html", **extra):
        if "orderable" not in extra:
            extra["orderable"] = True
        super().__init__(template_name=template_name, **extra)

    def render(self, record, table, value, bound_column, **kwargs):
        self.extra_context["view"] = table.view
        self.extra_context["uuid_short"] = str(value).split("-")[0]
        return super().render(record, table, value, bound_column, **kwargs)


class UUIDLinkDetailColumn(LinkDetailColumnMixin, UUIDColumn):
    pass


class NaturalTimeColumn(tables.TemplateColumn):

    def __init__(self, template_code=None, template_name="crud_views/columns/naturaltime.html", **extra):
        from .table import Table

        if "attrs" not in extra:
            extra["attrs"] = Table.ca.w10

        super().__init__(template_code=template_code, template_name=template_name, **extra)


class NaturalDayColumn(tables.TemplateColumn):

    def __init__(self, template_code=None, template_name="crud_views/columns/naturalday.html", **extra):
        from .table import Table

        if "attrs" not in extra:
            extra["attrs"] = Table.ca.w10

        super().__init__(template_code=template_code, template_name=template_name, **extra)
