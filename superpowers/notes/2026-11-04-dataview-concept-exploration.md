# Concept exploration: DataView (embedded tables and card lists)

Analysis only; no code changed. Every claim points at code. Paths without a repository prefix are in
`jacob-consulting/django-crud-views`, branch `claude/lucid-knuth-x5ity9` @ `cf2bfc0`. `tabler-test` is
`alexander-jacob/tabler-test` @ `506ed89`. django-tables2 is 3.0.1 (installed), Django 5.2.

## 1. The ask

A component, working name `DataView`, that shows data as a table or a card list, several of them on one page.
The Acme Roasters dashboard is the reference: a table "Orders to roast this week" next to a card-ish list "Recent
cuppings" (`tabler-test/example/dashboard/templates/dashboard/index.html:62-109`). What makes it different from a
list or card page:

- a fixed number of rows, no paging;
- no ordering controls.

Wanted: configurable from scratch (model or queryset plus configuration) or derived from an existing
`ListView` / `CardListView` of a ViewSet (`DataView.from_list_view(...)`). Open: permissions, and how the component
is initialised from a page's context.

## 2. What the code gives us today

### 2.1 The two dashboard widgets, as they are

Both reference widgets are hand-written, and both are **cross-parent**: their rows belong to different parents of a
nested ViewSet.

- Orders to roast: rows are `Order` objects across customers; the queryset is scoped by the user's Guardian grants
  (`customers_for(user)`, `tabler-test/example/dashboard/views.py:36-37, 63-68`); each row links to
  `reverse("order-detail", customer_pk=order.customer_id, pk=order.pk)` (`index.html:71`). `cv_order` is a child of
  `customer` (`example/sales/views/orders.py:38-48`); the top-level `cv_all_orders` ViewSet exists for the same
  reason and its table hand-rolls the same reverse (`orders.py:92-103`).
- Recent cuppings: `CuppingSession[:5]`, gated by `perms.roastery.view_greenlot` (`views.py:100-106`), each row
  links to `cupping-detail` with `lot_pk=session.lot_id` (`index.html:95`). The session ViewSet is a child of the
  lot (`example/roastery/views.py:198-206`).

So "a row's URL needs the parent pk taken from the row object" is not an edge case; it is both examples.

### 2.2 Everything in a list page runs through the view *instance*

- Sibling URLs: `cv_get_router_and_args` reads every parent pk from `self.kwargs` and raises
  `ValueError("kwarg X not found")` when it is missing (`src/crud_views/lib/view/base.py:580-586`). The one
  precedent for "URL from the object alone" is `DeleteView.cv_get_related_object_url`, which builds the kwargs from
  `getattr(obj, viewset.parent.get_attribute())` and catches `NoReverseMatch`
  (`src/crud_views/lib/views/delete.py:186-204`); it handles one parent level only.
- Querysets: `ViewSet.get_queryset(view)` filters by `view.kwargs[pk_name]` for every parent level
  (`src/crud_views/lib/viewset/__init__.py:277-305`), so a nested view's `get_queryset()` fails without URL kwargs.
  Guardian scoping is also a view method: `GuardianQuerysetMixin.get_queryset` wraps the ViewSet queryset with
  `get_objects_for_user` (`src/crud_views_guardian/lib/mixins.py:186-198`). Resources go through
  `ResourceViewMixin.get_queryset` → `model.cv_get_items(request, **kwargs)` (`src/crud_views/lib/resource.py:159-160`).
- Action buttons: row actions are `cv_get_list_action_group(obj)` → `cv_resolved_actions` → `cv_get_context` →
  `cv_resolve_action` (`base.py:636-665`, `src/crud_views/lib/view/visibility.py`); card actions are
  `cv_get_card_action_group(obj)` (`src/crud_views/lib/views/card.py:45-107`). All need `self.request` (user) and
  `self.kwargs` (parent pks for URLs).
- Labels: `cv_get_dict` reads `context.router_name` → `view.request.resolver_match.url_name` (`base.py:486`,
  `src/crud_views/lib/view/context.py:47-49`), so even a label needs a view bound to a request. The navigation
  notes already recorded this as the missing request-free label API (`2026-11-02-navigation-concept-exploration.md`,
  2.4).
- Template tags: every tag goes through `cv_get_view(context)`, which asserts `context["view"]` is a `CrudView`
  (`src/crud_views/templatetags/crud_views.py:72-75`). On a dashboard `view` is the dashboard's function or class, so
  `{% cv_card object %}`, `{% cv_list_action_group %}` etc. cannot be used as they are.
- Binding a view to a request is one Django call: `View.setup(request, *args, **kwargs)` sets `request`, `args`,
  `kwargs` (`django/views/generic/base.py:126-132`); `as_view()` does nothing more before `dispatch`. The package
  already binds a copy of a view to a different request in `_cv_cancel_owner` (`base.py:840-849`).

### 2.3 The table already carries its own view

`Table.__init__` requires `view=` (`src/crud_views/lib/table/table.py:14-20`); `ListViewTableMixin.get_table_kwargs`
passes `{"view": self}` (`src/crud_views/lib/views/mixins.py:259-260`). `ActionColumn.render` puts `table.view` into
the column's `extra_context` (`src/crud_views/lib/table/columns.py:24-26`), and `columns/actions.html` calls
`{% cv_list_action_group record %}` on it. So the row actions of a rendered table come from **the table's view, not
the page's `view` variable**. A table built with a request-bound list view instance renders correct row actions on
any page. `{% render_table table %}` only needs `context["request"]` (`django_tables2/templatetags/django_tables2.py`,
`RenderTableNode.render`).

The card path is not self-contained: `{% cv_card obj %}` builds `{"object", "view", "request"}` from
`cv_get_view(context)` (`templatetags/crud_views.py:505-516`), so a card tag for a DataView must take the view
explicitly.

### 2.4 "Fixed rows, no ordering" is already expressible

- Tables: `Table(..., orderable=False)` removes the sort links (`table/bootstrap5.html:14-21` renders a link only
  for `column.orderable`); `RequestConfig(request, paginate=False)` skips pagination
  (`django_tables2/config.py`), and `TableMixinBase.get_table_pagination` returns `False` when
  `table_pagination = False` (`django_tables2/views.py`). Both stock and Tabler table templates render the pager only
  when `table.page` is set (`table/bootstrap5.html:53`, `tabler-test/src/crud_views_tabler/templates/crud_views/table/bootstrap5.html`).
- Cards: `card_order.html` renders nothing without `view.cv_order_fields` (`snippets/card_order.html:3`);
  `{% cv_pagination %}` renders nothing without `is_paginated` (`snippets/pagination.html:2`); `paginate_by = None`
  is already the card default (`card.py:24`).
- The slice is `queryset[:n]`; `MultipleObjectMixin.get_context_data` uses `self.object_list` when it is set.
- The content partials are already separated from the page: `view_list_table.content.html` is just
  `{% render_table table %}`; `view_card.content.html` is the card grid plus order bar and pager. They are the
  `cv_content_template` the modal path reuses (`base.py:109`, "shared by full page and modal").

### 2.5 Permissions: the three layers exist, and which one applies

| Layer | Mechanism today | Applies to a DataView how |
|---|---|---|
| Page/request gate | `CrudViewPermissionRequiredMixin.has_permission` (`base.py:912-924`), Guardian `dispatch` parent gate (`mixins.py:262-277`) | **Not at all**: a DataView is rendered inside another page's request; nothing dispatches it. The page that hosts it is gated by its own view. |
| Link visibility | `cls.cv_has_access(user, obj)` + `cls.cv_action_enabled(user, obj)` (`base.py:353-367, 926-930`), the rule every toolbar/row/card button uses; Guardian list: signed-in and active (`mixins.py:130-131`) | **Widget visibility**: `cv_has_access(user, None) and cv_action_enabled(user, None)` of the source list view is exactly the rule the toolbar's `list` button and the nav (decision 2, nav notes §7) use. Plain Django perms for a from-scratch widget: `user.has_perm("app.view_x")`, which is what the mixin does with `viewset.permissions["view"]`. |
| Row scope | the view's `get_queryset()` (ViewSet parent filter, Guardian `get_objects_for_user`, the view's own `select_related`) | **Row scope**: inherited only when the DataView calls `view.get_queryset()`; a supplied queryset is the project's responsibility (the dashboard's `customers_for(user)` is that case). |
| Per-row actions | `cv_get_list_action_group` / `cv_get_card_action_group` → `cv_resolve_action` (hide, or disable under `inaccessible_actions="disable"`) | unchanged, as soon as the group methods run on a request-bound view instance. |

Two consequences:

1. The package already states the principle that applies: hiding is presentation, the request is protection
   (`docs/reference/theme.md`, "Authorized data in overridden templates"). A DataView's own gate is presentation;
   its rows are protected by the queryset it is given. A from-scratch DataView over a raw `Model.objects.all()`
   on a Guardian-scoped model leaks by construction; the docs must say which queryset to pass.
2. The two `cv_has_access` gaps recorded as decision 6 of the navigation notes (missing permission row → `True`;
   Guardian child list ignores the parent gate) are inherited by a DataView exactly like by the nav. They stay a
   prerequisite.

A third, smaller point: `cv_get_link_url` tags every sibling link with `cv_origin=<this view's cv_key>` and a cancel
token (`base.py:1000-1018`), so an "update" link rendered inside a widget sends Cancel back to the *list page*, not to
the dashboard. The widget must either carry no origin (`cv_get_link_origin_key` returns None when
`self.cv_key` is not in the target's keys) or a page-URL origin, which does not exist yet.

### 2.6 Theming surface a DataView touches

- The table and the cards render through templates the Tabler theme already overrides
  (`crud_views/table/bootstrap5.html`, `tags/card.html`, `view_card.content.html`,
  `tabler-test/src/crud_views_tabler/templates/crud_views/`). Row and card buttons keep locations `list` / `card`,
  so no new button location is needed; `LOCATIONS` stays closed (`src/crud_views/lib/view/button_data.py:19`).
- New: the **frame** (a box with a title, the body, an optional "all …" link to the full list). Precedent is the
  card frame: `card:root`, `card:body`, `card:title` keys in `DEFAULT_BUTTON_CLASSES`
  (`src/crud_views/lib/button_classes.py:91-93`) plus a leaf with blocks (`tags/card.html`, #243). A
  `dataview:root/header/title/body/footer` key set must ship in the default table or W362 fires for themes
  (`button_classes.py:301-319`). Tabler's frame is `.card > .card-header > .card-title`, body `.table-responsive`
  or `.list-group-flush` (`index.html:63-66, 91-93`).
- Stability: new names land as provisional after 1.0, the rule set for the nav (nav notes §7, decision 5;
  `docs/development/stability.md:7-17`).

### 2.7 Precedents for the mechanics

| Need | Precedent |
|---|---|
| Component resolved from the registry by name | `ViewSet.get_viewset(name).get_view_class(key)` (`viewset/__init__.py:160-164, 336-343`) |
| Per-page component from a view mixin, cached on the view | `CrudViewBreadcrumbMixin.cv_breadcrumb` / `get_context_data` (`src/crud_views/lib/breadcrumb.py:151-155, 280-283`) |
| Render a partial with its own context and `request=` | `cv_card` (`templatetags/crud_views.py:505-516`), `cv_render_button` (`:218-229`) |
| Object-only URL for a nested view | `DeleteView.cv_get_related_object_url` (`delete.py:186-204`) |
| Declarative, validated configuration | `CardAction`, `ContextButton`, `BreadcrumbItem` (Pydantic) |
| Views that render no page header | `cv_backend_only` (#179, `base.py:76-78, 150-154`) |
| Fetching a partial of a view into another page | the modal path: `X-CV-Modal` header, `crud_views/modal/content.html`, `cv_content_template` (`base.py:218-221`) |

## 3. Decisions independent of the approach

### 3.1 Prerequisite P1: sibling URLs from the object when the kwargs are missing

Every approach needs row links for cross-parent rows (2.1). Proposed: in `cv_get_router_and_args`, when a parent
kwarg is not in `self.kwargs`, derive it from the object by walking `ParentViewSet.get_attribute()` up the chain
(the loop `ViewSet.get_queryset` already walks for filtering, `viewset/__init__.py:285-295`), raising only when
neither source has it. Generalises `cv_get_related_object_url` to every parent level and benefits every list page
that shows rows of mixed parents (tabler-test's `AllOrdersTable.render_number` would go away). M2M nesting
(`many_to_many_through_attribute`) has no single parent per row; it keeps today's error.

### 3.2 Prerequisite P2: the two `cv_has_access` gaps

Unchanged from the nav notes §9 (phase 6.5). A DataView over a Guardian child list without them advertises rows the
request refuses.

### 3.3 Widget visibility rule

`cls.cv_has_access(user, None) and cls.cv_action_enabled(user, None)` of the source view; hidden by default, or an
empty frame with a disabled look under `inaccessible_actions="disable"` (same knob as buttons,
`base.py:263-270`). From-scratch widgets name a permission string or a callable; `None` means always visible.

### 3.4 Origin of links inside a widget

Decide: links carry no `cv_origin` (Cancel/success fall back to the targets' static keys), or a new "page URL"
origin. Recommended for v1: no origin; the dynamic-cancel machinery is key-based by design (`base.py:966-998`).

## 4. The approaches

### Approach A: bound view instance ("the list view is the component")

A `DataView` wraps an *instance* of an existing list or card view class, bound to the page's request with
`View.setup`, with paging and ordering switched off and the queryset sliced. Row actions, labels, Guardian
scoping, card templates and the theme come from the view class unchanged; the package adds one small class, one
tag and one frame leaf.

```python
# crud_views/lib/dataview.py (sketch)
from django.template.loader import get_template
from django.utils.safestring import mark_safe

from crud_views.lib.viewset import ViewSet
from crud_views.lib.views.card import CardListView


class DataView:
    def __init__(self, view_class, request, *, queryset=None, limit=5, title=None, kwargs=None, mode=None):
        view = view_class()
        view.setup(request, **(kwargs or {}))     # django.views.generic.base.View.setup: request/args/kwargs
        view.paginate_by = None                   # MultipleObjectMixin: no page_obj / is_paginated
        view.table_pagination = False             # TableMixinBase.get_table_pagination() -> False
        view.cv_order_fields = []                 # CardOrderMixin: card_order.html renders nothing
        qs = queryset if queryset is not None else view.get_queryset()   # Guardian + parent filter inherited
        view.object_list = qs[:limit]
        self.view, self.title, self.limit = view, title, limit
        self.mode = mode or ("card" if isinstance(view, CardListView) else "table")

    @classmethod
    def from_viewset(cls, name, key="list", **kwargs):
        """Resolve the view class from the registry, so a page never imports view modules."""
        return cls(ViewSet.get_viewset(name).get_view_class(key), **kwargs)

    @property
    def cv_access(self) -> bool:
        cls, user = type(self.view), self.view.request.user
        return bool(cls.cv_has_access(user, None) and cls.cv_action_enabled(user, None))

    @property
    def cv_list_url(self) -> str | None:
        """'All …' link to the full page; None for a nested ViewSet without kwargs or without access."""
        try:
            return self.view.cv_get_url(self.view.cv_key) if self.cv_access else None
        except ValueError:
            return None

    def get_context(self) -> dict:
        view = self.view
        context = {"view": view, "request": view.request, "object_list": view.object_list, "cv_dataview": self}
        if self.mode == "table":
            # SingleTableMixin.get_table: Table(data=object_list, view=view, orderable=False) + RequestConfig(paginate=False)
            context["table"] = view.get_table(orderable=False, **view.get_table_kwargs())
        return context
```

```python
# templatetags/crud_views.py
@register.simple_tag(takes_context=True)
def cv_dataview(context, dataview):
    if not dataview.cv_access:
        return ""   # or the disabled frame under inaccessible_actions="disable"
    template = get_template(f"{crud_views_settings.theme_path}/tags/dataview.html")
    return mark_safe(template.render(dataview.get_context(), request=context["request"]))
```

```django
{# crud_views/tags/dataview.html: the frame leaf; blocks like tags/card.html (#243) #}
{% load crud_views %}
<div class="{% cv_button_class 'dataview' 'root' %}">
  <div class="{% cv_button_class 'dataview' 'header' %}">
    {% cv_button_class 'dataview' 'title' as t %}{% cv_heading level=3 class=t %}{% block dataview_title %}{{ cv_dataview.title }}{% endblock %}{% endcv_heading %}
    {% if cv_dataview.cv_list_url %}<a href="{{ cv_dataview.cv_list_url }}">{% block dataview_all %}…{% endblock %}</a>{% endif %}
  </div>
  {% block dataview_body %}{% include view.cv_content_template %}{% endblock %}
</div>
```

`view.cv_content_template` is `view_list_table.content.html` (`{% render_table table %}`, so the Tabler card-table)
or `view_card.content.html` (cards through `{% cv_card object %}`, which works here because `view` in this context
*is* the bound CrudView).

Page side, three equally grounded ways to initialise it (the "context" question):

```python
# (i) in the page view: explicit, testable, the queryset is visibly the project's
def index(request):
    ...
    context["orders_widget"] = DataView.from_viewset(
        "orders", request=request, queryset=to_roast, limit=10, title=_("Orders to roast this week")
    )
```

```django
{# (ii) in the template, from a queryset the page already has: no Python in the page view #}
{% cv_dataview_for "orders" queryset=orders_to_roast limit=10 title=_("Orders to roast this week") %}
```

```python
# (iii) a page mixin, breadcrumb-style: declared once, resolved lazily in get_context_data
class DashboardView(DataViewsMixin, TemplateView):
    cv_dataviews = {
        "orders_widget": DataViewSpec(viewset="orders", limit=10, title=_("Orders to roast this week"),
                                      queryset="get_orders_to_roast"),   # method name, called with the request
        "cuppings_widget": DataViewSpec(viewset="session", key="card", limit=5),
    }
```

| Aspect | Pro | Con |
|---|---|---|
| From list view | one line: the class *is* the configuration; filters, `select_related`, Guardian scope, row actions, card template all inherited | the view class's other mixins run too: a `BreadcrumbMixin.get_context_data` would walk parents with empty kwargs, so the DataView must build its own context and never call `get_context_data()` (the sketch does) |
| From scratch | "from scratch" = a small `ListView`/`CardListView` subclass registered on the ViewSet (`cv_backend_only=True`, a `cv_card_template`, `cv_card_actions`), no second configuration model | a widget over a model with no ViewSet needs a ViewSet anyway (URLs, permissions come from it); for pure display with no actions, a plain template is still simpler |
| Permissions | identical to the toolbar's rule; nothing new to document except the queryset responsibility | inherits P2; visibility is presentation only |
| Context init | (i)–(iii) all work; the registry lookup avoids importing view modules into page code | the bound instance has no URL kwargs: nested ViewSets need P1 for row links and an explicit queryset |
| Theme | table/cards already themed; one new frame leaf and five class keys | frame keys join the W362 vocabulary |
| Fit | reuses `View.setup`, `cv_content_template`, `get_table`, `cv_card`; smallest new surface | the instance is a view that never dispatched: no `_cv_consume_cancel_restore`, origin links point at the list page (3.4) |

### Approach B: standalone declarative component ("DataView is a model of its own")

A Pydantic/plain class describing the widget, with its own resolver: model or queryset, columns or card template,
actions, permission, limit; `from_list_view` copies `table_class`, `cv_card_template`, `cv_card_actions`,
`cv_list_actions` from a view class.

```python
class RecentCuppings(DataView):
    model = CuppingSession
    viewset = "session"                                  # for action URLs; default: registry lookup by model
    title = _("Recent cuppings")
    mode = "card"
    card_template = "roastery/cupping_card.html"
    actions = [CardAction(key="detail")]
    permission = "roastery.view_cuppingsession"         # str, callable(user) -> bool, or None
    limit = 5

    def get_queryset(self, request):
        return CuppingSession.objects.select_related("lot__origin").prefetch_related("scores")
```

The resolver has to reproduce, per row: the target class (`viewset.get_view_class(key)`), the URL (P1), access
(`cls.cv_has_access(user, obj)`), state (`cls._cv_action_enabled_for_rendering(user, obj, rendering_view)`, which
takes a rendering view), labels (`cls.cv_get_dict(context)` needs a `ViewContext` with a request-bound view,
`context.py:16, 47-49`) and the hidden POST forms / modal triggers (`tags/list_action_form.html`). Every one of these
is a view method today, so B either builds a throw-away bound view internally (then it is A with a facade) or adds
a request-free parallel API, which the nav notes already identified as missing and expensive (nav §2.4).

| Aspect | Pro | Con |
|---|---|---|
| From list view | a copy of attributes, no instance of foreign mixins | the copy drifts: a view's `get_queryset` override, `get_table_kwargs`, label-mode choices and Guardian mixins are not attributes; `from_list_view` silently loses them |
| From scratch | the cleanest declaration; works for a model without a ViewSet when there are no actions | with actions it needs a ViewSet anyway |
| Permissions | explicit `permission` is easy to read | a second permission vocabulary next to `cv_permission`; parity with the toolbar is a test burden, the problem the nav notes warn about for `perms` |
| Context init | the object is request-free until `render(request)`; (i)–(iii) all possible | the resolver still needs a bound view for labels and actions |
| Theme | same frame leaf; may render its own row markup | if it renders its own rows it bypasses `render_table` / `cv_card` and the Tabler overrides |
| Fit | reads like `ContextButton`/`CardAction` | the largest surface: a parallel action/URL/label path to keep in step with `base.py` |

### Approach C: a registered sibling view ("the widget has a URL")

The widget is a real view on the ViewSet (`cv_key="widget_to_roast"`, `cv_path="widgets/to-roast"`,
`cv_object=False`, `cv_backend_only=True`) rendering only its content partial. The dashboard includes it server-side
(A's binding, now with the view's own kwargs) or lazily: a placeholder `<div data-cv-dataview="<url>">` that
`viewset.js` fetches the way the modal path fetches `cv_content_template` (`X-CV-Modal`, `modal/content.html`).

```python
class OrdersToRoastWidget(DataViewMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_all_orders
    cv_key = "widget_to_roast"
    cv_path = "widgets/to-roast"
    cv_backend_only = True
    cv_permission = "view"
    table_class = AllOrdersTable
    cv_dataview_limit = 10
    cv_dataview_title = _("Orders to roast this week")

    def get_queryset(self):
        return orders_to_roast(self.request.user)
```

```django
{% cv_dataview "orders" "widget_to_roast" %}          {# server-side include, bound to this request #}
{% cv_dataview "orders" "widget_to_roast" lazy=True %} {# placeholder + fetch #}
```

| Aspect | Pro | Con |
|---|---|---|
| From list view | subclass the list view, set the limit: the parity is by inheritance | one class and one URL per widget |
| From scratch | the same declaration shape as every other view; system checks cover it (`checks()`) | a widget over a model without a ViewSet needs one |
| Permissions | the **real request gate** applies when fetched lazily (`has_permission` → 403), plus the link rule for the include | a nested ViewSet's widget URL carries parent pks, so a cross-parent widget must live on a top-level ViewSet (tabler-test has `cv_all_orders` for exactly this) |
| Context init | the tag needs only names; nothing in the page view | lazy loading means a second render path, JS, and a loading state to theme |
| Theme | content partials as today; frame leaf as A | the placeholder is a new leaf |
| Fit | precedent in modals and `cv_backend_only`; URLs enable refresh/htmx later | server-side include still needs A's binding; lazy fetch adds JS to a package whose JS surface is being frozen |

## 5. Comparison at a glance

| Requirement | A: bound instance | B: declarative | C: registered sibling |
|---|---|---|---|
| from a ListView/CardListView | instance of the class | attribute copy (lossy) | subclass |
| from scratch | small view subclass on a ViewSet | own class, ViewSet only for actions | view subclass on a ViewSet |
| fixed rows, no ordering | slice + `paginate=False` + `orderable=False` + `cv_order_fields=[]` | own rendering | same as A |
| widget permission | `cv_has_access(user, None)` + `cv_action_enabled` | `permission` field | request gate (lazy) or link rule (include) |
| row scope | `view.get_queryset()` or supplied | `get_queryset(request)` | `get_queryset()` |
| row actions | inherited | re-implemented | inherited |
| cross-parent rows | needs P1 | needs P1 | needs P1, widget on a top-level ViewSet |
| context initialisation | page view, tag, or mixin | same | tag by name |
| new public surface | `DataView`, one tag, one leaf, five keys | class + resolver + tag + leaf | mixin + tag(s) + leaf + JS |

## 6. Recommendation

A as the core, with C's registration as the "from scratch" shape and as the later lazy-load path:

1. P1 and P2 first (both are small and pay off outside DataView).
2. `DataView` = a request-bound list/card view instance plus a frame (approach A), resolved from the registry by
   name; page-view initialisation (i) in v1, the tag (ii) as sugar, the mixin (iii) only if a consumer asks.
3. "From scratch" = declare a small list/card view on the ViewSet; `cv_backend_only=True` keeps it off the
   header/paragraph checks. No parallel configuration model (B) because every row feature is a view method.
4. Lazy loading (C) is a later, separate decision; the registered view then already exists.

Why not B: it would be the second place that resolves actions, URLs and labels, and the nav exploration showed
that path only works with a request-bound view anyway.
