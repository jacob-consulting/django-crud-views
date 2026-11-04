> **Historical proposal — prerequisite strategy superseded on 2026-11-04.** The maintainer chose an opt-in URL helper and cancelled integrated phase 06.10. See the [decision and document index](../notes/2026-11-04-opt-in-url-helper-decision.md) before planning from this document. The original document is preserved below.

# DataPanel: embedded tables and card lists — design

Date: 2026-11-04. Status: draft for approval. Concept exploration with code references:
`superpowers/notes/2026-11-04-dataview-concept-exploration.md`. Prerequisite issues: #311 (parent pks derived from the
object) and #312 (link visibility agrees with the request gate). Name decided 2026-11-04: `DataPanel` (the concept
note uses the working name DataView); see "Decisions".

## Intent

A page that is not a crud page (a dashboard, a start page, a detail page of another model) shows one or more small
lists of crud objects: a table "Orders to roast this week", a card list "Recent cuppings". Each list is a fixed number
of rows, with no paging and no ordering controls, and each row keeps the crud-views machinery: links and action
buttons that point at the right sibling views, with the same visibility rules as on the list page, and the theme's
table or card markup.

Today such a page is written by hand (`tabler-test/example/dashboard/templates/dashboard/index.html`): its own
`<table>`, its own `reverse()` calls with hand-picked parent pks, its own `{% if perms.… %}`. Nothing of the ViewSet
is reused, and every rule the package already has (what a row links to, who sees which action, how a theme renders a
table) is reimplemented per page.

The reason behind the feature: the package should be the one place where "how this model's rows look and link" is
defined, and a dashboard should consume that definition rather than copy it.

## Goals

- A DataPanel built from an existing `ListView` (django-tables2) or `CardListView` of a ViewSet in one expression,
  bound to the current request, inheriting the view's table or card template, row/card actions, Guardian queryset
  scope and the theme.
- A DataPanel "from scratch": a small view declared for the widget alone, with its own table or card configuration,
  without copying any package machinery.
- A fixed number of rows (`limit`), no pagination, no sort links, no card-order bar.
- Several DataPanels on one page, each with a frame (title, body, optional link to the full list), themable through
  the class table and one overridable leaf.
- Widget visibility follows the same rule as a toolbar button pointing at the list view: `cv_has_access` and
  `cv_action_enabled` of the source view, evaluated for the request's user.
- Row links work for rows of mixed parents (after #311).
- Initialisation from a page view, or from a template with a queryset the page already has.

## Non-goals

- Paging, ordering, filtering inside a DataPanel. A user who wants those follows the "all" link to the list page.
- Lazy loading or refresh through a fetched URL (approach C's second half). The design keeps the door open: a
  from-scratch widget is a registered view and therefore has a URL; the fetch path is a later, separate decision.
- A request-free label or action API. Labels and actions keep needing a request-bound view; that is why the DataPanel
  is built on one.
- A navigation component, or any dashboard layout system. The DataPanel is one box; the page lays out the boxes.
- Charts, stat tiles, or any non-list widget.
- Changing the core contract that the parent URL part is checked by scope, not permission (noted in #311).

## Anti-goals

- A second configuration model that mirrors view attributes (`columns`, `actions`, `permission`) and drifts from the
  view class. Every row feature stays a view attribute or method; the DataPanel only binds and frames.
- Any new permission vocabulary. Visibility is `cv_has_access` + `cv_action_enabled`; row scope is the queryset.
- Calling the source view's `get_context_data()`. Foreign mixins on real list views (breadcrumb, filter persistence)
  assume a dispatched request with URL kwargs; the DataPanel builds its own minimal context.
- Markup of its own for rows. Tables render through `{% render_table %}`, cards through `{% cv_card %}`, so the
  theme's overrides apply unchanged.
- A new button location. Row and card buttons keep `list` / `card`; `LOCATIONS` stays closed.

## Constraints

- Every URL, label, access check and action group is a method of a `CrudView` *instance* needing `request` and
  `kwargs` (`base.py:576-609`, `:486`, `:636-665`). Django's `View.setup(request, *args, **kwargs)` is the binding.
- A nested ViewSet's `get_queryset()` and sibling URLs need parent pks. Without URL kwargs: the queryset must be
  supplied by the page, and row links need #311. The "all" link of a nested list is only resolvable with kwargs.
- Template tags resolve the view through `context["view"]`; the DataPanel renders its leaf with its own context in
  which `view` is the bound instance, so `{% cv_card %}` and `columns/actions.html` work unchanged.
- The theme class table warns (`W362`) for keys outside `DEFAULT_BUTTON_CLASSES`; new keys ship in the default table.
- New public names land after 1.0 as provisional (navigation decision 5): no deprecation obligation until two
  consumers (core example, Tabler theme) have rendered them.
- Link origin: `cv_get_link_url` tags sibling links with `cv_origin=<this view's key>` and a cancel token; from a
  widget that would send Cancel to the list page. Widget links carry no origin.

## Approaches considered

| | A: bound view instance | B: standalone declarative class | C: registered sibling view |
|---|---|---|---|
| Shape | wrap an instance of the existing list/card view class, bound to the request; slice, switch paging/ordering off, frame it | own class with model/queryset, columns or card template, actions, permission; own resolver | the widget is a registered view (`cv_key`, `cv_backend_only`) rendering only its content partial; included server-side or fetched lazily |
| From a list view | the class *is* the configuration; overrides, Guardian mixins, label modes inherited | attribute copy, lossy (`get_queryset`, `get_table_kwargs`, mixins are not attributes) | subclass |
| From scratch | a small view on the ViewSet | cleanest declaration, but with actions it needs a ViewSet anyway | the same declaration as every view |
| Permissions | the toolbar's rule, nothing new | a second vocabulary to keep in parity | the real request gate when fetched |
| Cost | one class, one tag, one leaf, five keys | a parallel action/URL/label path next to `base.py` | plus JS and a loading state |

Chosen: **A for v1, with C's registered shape as the "from scratch" form and as the reserved path for lazy loading
later.** B was dropped because every row feature is a view method today; B would either hide an A instance behind a
facade or add the request-free API the navigation exploration already found missing and expensive.

## The design

### 1. `DataPanel` (`crud_views/lib/datapanel.py`)

```python
class DataPanel:
    def __init__(
        self,
        view_class: type[CrudView],
        request,
        *,
        queryset=None,            # None: view.get_queryset() (needs kwargs for a nested ViewSet)
        limit: int = 5,
        title=None,               # None: the view's cv_header (the list page title)
        kwargs: dict | None = None,   # URL kwargs for the bound view (a widget on a nested page passes its own)
        mode: str | None = None,  # "table" | "card"; None: "card" for CardListView, else "table"
        view_attrs: dict | None = None,   # instance attributes, validated like as_view() initkwargs
        row_actions: bool = True, # False: no action column / no card actions
        list_link: bool = True,   # the "all …" link to the ViewSet's list page, when resolvable and accessible
        empty_text=None,          # None: the package's translated "No items found."; honoured in both modes
        id: str | None = None,    # element-id namespace; None: "dv<N>" per request
    ): ...

    @classmethod
    def from_viewset(cls, name: str, key: str = "list", **kwargs) -> "DataPanel":
        """ViewSet.get_viewset(name).get_view_class(key), so a page never imports view modules.
        "list" falls back to "card" as everywhere."""

    view: CrudView          # the bound instance
    mode: str
    title: str
    limit: int

    @property
    def cv_access(self) -> bool:
        """type(view).cv_has_access(user, None) and type(view).cv_action_enabled(user, None): the toolbar's rule."""

    @property
    def cv_list_url(self) -> str | None:
        """The ViewSet's list page, never the widget's own URL: view.cv_get_url("list") ("list" falls back to
        "card" as everywhere), when list_link is set, the key is registered, the URL is resolvable (ValueError →
        None: a nested ViewSet without kwargs) and the *list view class* passes cv_has_access(user, None) and
        cv_action_enabled(user, None). A registered widget view (cv_key "widget_recent") therefore links to the
        same page as a derived one."""

    id: str
    """Per-page namespace for element ids: the ``id=`` argument, else "dv<N>" counted per request (the counter
    lives on the request object). Two widgets of one ViewSet on one page would otherwise emit the same
    ``cv_form_<oid>`` ids: cv_get_oid is ``<viewset>_<key>_<pk>`` because a crud page shows one list."""

    def get_context(self) -> dict:
        """{"view", "request", "object_list", "cv_datapanel", and "table" in table mode}."""
```

Binding, in order: `view = view_class()`, `view.setup(request, **kwargs)`, apply `view_attrs`, then
`view.cv_link_origin = False`, `view.cv_oid_prefix = self.id`, `view.paginate_by = None`,
`view.table_pagination = False`, `view.cv_order_fields = []`, then the queryset:
`queryset if queryset is not None else view.get_queryset()`, sliced to `limit`, stored as `view.object_list`. Table
mode builds the table once in `get_context()` through the view's own `get_table(orderable=False, **get_table_kwargs())`,
so `get_table_kwargs` overrides and `table_class` apply; `row_actions=False` adds `exclude=("actions",)` to the table
kwargs (the convention of `crud_views.lib.table.Table`) and sets `cv_card_actions = []` in card mode.

`empty_text` is honoured in both modes: `Table(empty_text=…)` for tables; for cards the DataPanel puts it into the
leaf context as `cv_empty_text`, and the stock `view_card.content.html` renders `cv_empty_text` when set, else its
translated "No items found." (a one-line change to that stock template; list pages never set the variable, so the
card goldens stay byte-identical; the Tabler override of that template gets the same line as a downstream follow-up).

Element ids: a new `CrudView` attribute `cv_oid_prefix: str | None = None`; `cv_get_oid` returns
`<prefix>_<viewset>_<key>_<pk>` when it is set, else today's value. The DataPanel sets it on the bound instance, so
hidden POST forms and their `form=` buttons stay paired per widget. The frame root carries `id="cv-datapanel-<id>"`.

`view_attrs` are validated like Django's `as_view()` initkwargs: every key must be an existing attribute of the
class, else `TypeError`. This is the per-widget knob for `cv_list_actions`, `cv_list_actions_inline`,
`cv_card_actions`, `cv_card_container_class`, `cv_card_template`, label modes and the like.

Mode: `"card"` needs a `CardListView` (it has `cv_get_card_action_group` and `cv_card_template`); `"table"` needs
`get_table` (a `ListViewTableMixin` view). Anything else raises `ImproperlyConfigured` naming both options.

Visibility: a DataPanel whose `cv_access` is false renders nothing. There is no "disabled frame" variant; the page
can read `cv_access` and render its own placeholder. (Maintainer call; see below.)

Origin: a new `CrudView` attribute `cv_link_origin: bool = True`; `cv_get_link_origin_key` returns `None` when it is
false. The DataPanel sets it on the bound instance, so widget links carry neither `cv_origin` nor a cancel token and
the targets' static Cancel/success keys apply. Documented in `docs/reference/context_buttons.md` next to the origin
description.

### 2. Template tags (`crud_views/templatetags/crud_views.py`)

```django
{% cv_datapanel widget %}
{% cv_datapanel_for "orders" queryset=orders_to_roast limit=10 title=_("Orders to roast this week") %}
```

`cv_datapanel` renders a DataPanel: nothing when `cv_access` is false, else the frame leaf rendered with
`datapanel.get_context()` and `request=context["request"]` (a `RequestContext`, as `cv_card` does, so
`{% csrf_token %}` inside action forms works). `cv_datapanel_for` is sugar: `DataPanel.from_viewset(name, key, request=
context["request"], **options)` then the same rendering; it accepts the constructor's keyword options except
`view_attrs` (a dict literal has no template syntax; use the page view for that).

### 3. The frame leaf (`crud_views/tags/datapanel.html`)

One overridable template with blocks, like `tags/card.html` (#243):

```django
{% load crud_views %}
<div id="cv-datapanel-{{ cv_datapanel.id }}" class="{% cv_button_class 'datapanel' 'root' %}" cv-datapanel="{{ view.cv_viewset.name }}:{{ view.cv_key }}">
  {% block datapanel_header %}
  <div class="{% cv_button_class 'datapanel' 'header' %}">
    {% cv_button_class 'datapanel' 'title' as cv_title_class %}{% cv_heading level=3 class=cv_title_class %}{% block datapanel_title %}{{ cv_datapanel.title }}{% endblock %}{% endcv_heading %}
    {% block datapanel_link %}{% if cv_datapanel.cv_list_url %}<a class="{% cv_button_class 'datapanel' 'link' %}" href="{{ cv_datapanel.cv_list_url }}">{% translate "Show all" %}</a>{% endif %}{% endblock %}
  </div>
  {% endblock datapanel_header %}
  {% block datapanel_body %}<div class="{% cv_button_class 'datapanel' 'body' %}">{% include view.cv_content_template %}</div>{% endblock datapanel_body %}
  {% block datapanel_footer %}{% endblock datapanel_footer %}
</div>
```

`view.cv_content_template` is `view_list_table.content.html` (`{% render_table table %}`) or
`view_card.content.html` (the card grid; its order bar and pager render nothing because of the instance attributes).
The heading follows `CRUD_VIEWS_HEADER_LEVEL` like every content heading; `level=3` is the stock level while the
setting is unset (a widget is a section of its page).

Class keys, added to `DEFAULT_BUTTON_CLASSES` (Bootstrap 5 defaults): `datapanel:root` (`card mb-3`),
`datapanel:header` (`card-header d-flex align-items-center justify-content-between`), `datapanel:title`
(`card-title mb-0`), `datapanel:body` (`card-body p-0`), `datapanel:link` (`btn btn-link btn-sm`). Themes register
their values from `ready()`; projects override per key.

Leaf context contract (documented): `cv_datapanel` (`id`, `title`, `mode`, `limit`, `cv_list_url`, `cv_access`),
`view`, `request`, `object_list`, `table` (table mode), `cv_empty_text` (card mode, when set). The root's `id` and the
attribute `cv-datapanel="<viewset>:<key>"` are the hooks a later lazy-load path and tests use.

### 4. From scratch

A widget that is not an existing list or card view is a view declared for it. Two shapes, both documented:

- **Derived without a URL.** A subclass of a registered view of the ViewSet that does *not* set `cv_viewset` in its
  own body inherits it and is not registered (the metaclass registers only classes that set `cv_viewset`
  themselves, `src/crud_views/lib/view/meta.py`). It gets no URL and no system checks of its own, and it keeps the
  parent's table, filters out of the way and permissions:

  ```python
  class RecentSessions(SessionListView):           # inherits cv_viewset, not registered
      table_class = SessionCompactTable
      cv_list_actions = ["detail"]
  ```

- **Registered widget view** (approach C's shape). A view with its own `cv_viewset` and a key that is not `list`
  or `card` (those keys have fallback semantics), `cv_backend_only = True` so no header/paragraph templates are
  required, answering its URL as an ordinary page under the ordinary gate. This is the shape that can be fetched
  lazily later:

  ```python
  class RecentSessionCards(CardListViewPermissionRequired):
      cv_viewset = cv_session
      cv_key = "widget_recent"
      cv_path = "widgets/recent"
      cv_backend_only = True
      cv_permission = "view"
      cv_card_template = "roastery/session_card.html"
      cv_card_actions = [CardAction(key="detail")]
  ```

Either is bound with `DataPanel(RecentSessions, request, …)` or `DataPanel.from_viewset("session", "widget_recent", …)`.

### 5. Permissions, stated once in the docs

| Layer | Rule | Where it comes from |
|---|---|---|
| Widget visibility | `cv_has_access(user, None) and cv_action_enabled(user, None)` of the source view | the toolbar's "list" button rule; Guardian list: signed-in and active |
| Row scope | the queryset the DataPanel is given, or `view.get_queryset()` (ViewSet parent filter, Guardian filter, the view's own `select_related`) | the page's responsibility when supplied; the docs show `customers_for(user)` style scoping and say why |
| Row actions | `cv_get_list_action_group` / `cv_get_card_action_group` → `cv_resolve_action` (hide or disable) | unchanged |
| Request gate | none for the widget itself; the hosting page's view gates the request; a registered widget view's URL is gated like any view | `docs/reference/theme.md`, "hiding is presentation" |

Parity with the request gate for Guardian child links and undeclared permission rows is #312.

### 6. Docs, example, changelog, stability

- `docs/reference/datapanel.md` under "Lists & tables" in `docs/reference/.pages`: the two ways to build one, the
  from-scratch shapes, the permission table above, the leaf contract, the class keys, the nested/`kwargs` rule and
  the "all" link rule, `view_attrs`.
- `docs/reference/templates.md` base-template table: `{% cv_datapanel %}` next to `cv_breadcrumb`.
- `docs/reference/context_buttons.md`: `cv_link_origin`; `docs/reference/action_view.md` (hidden POST forms):
  `cv_oid_prefix`.
- `docs/development/stability.md`: `DataPanel`, `cv_datapanel`, `cv_datapanel_for`, `tags/datapanel.html` and the five
  keys listed as **provisional**; `cv_link_origin` and `cv_oid_prefix` under `CrudView`.
- `CHANGELOG.md` `### Added`.
- Example: one "Dashboard" page in the Bootstrap 5 example project with a table widget and a card widget
  (author table, author cards), placed by the maintainer of the examples restructure where it fits.
- Translations: "Show all" in `crud_views/locale/de`.
- Downstream, separate repo: `crud_views_tabler` registers the five keys and overrides `tags/datapanel.html`
  (`.card > .card-header > .card-title`, body `.table-responsive` for tables); the Acme dashboard replaces its two
  hand-written widgets. Both are follow-ups in `tabler-test`, tracked in its findings doc.

### 7. Tests (`tests/test1/`)

- Unit: construction on `RequestFactory` requests with a user; `from_viewset`; mode detection and the
  `ImproperlyConfigured` cases; `view_attrs` validation; `limit` slicing; `cv_access` for a user with/without the
  permission and for a Guardian list view (signed-in rule); `cv_list_url` for top-level, nested without kwargs
  (None), nested with kwargs, a registered widget view (points at the ViewSet's list, gated by the list class), a
  ViewSet without a list/card view (None); `id` explicit and auto-counted across two widgets on one request.
- Rendering: a test page view in `tests/test1/app` embedding an author table widget, an author card widget and a
  nested book widget with a supplied cross-parent queryset; assert no pager, no sort links, no order bar, the
  row/card actions of the source view, the root `id` and `cv-datapanel` attribute, distinct `cv_form_*` ids and
  `form=` targets across the two author widgets (one POST action key in `view_attrs`), no `cv_origin` in links,
  nothing rendered without access, `row_actions=False`, `empty_text` in both modes.
- Goldens under `tests/test1/golden/datapanel/` for the stock frame in both modes (same harness as
  `test_action_menus_golden.py`).
- Query count: a widget over a Guardian list view costs the same queries as the list page minus pagination; pinned
  with `django_assert_num_queries`.
- The nested book widget asserts cross-parent row links (#311 is a precondition, below).
- Existing goldens stay byte-identical: the only stock template changes are the new leaf and the guarded
  `cv_empty_text` line in `view_card.content.html`.

## Sequencing and preconditions

The plan is executed against a tree where all of the following are in; it lists them as preconditions and does not
work around any of them:

1. **#311 merged.** The nested book widget's row links need the object-derived parent pks; without it every row
   action in that fixture raises `ValueError`.
2. **#312 merged.** The widget's visibility promise ("the same rule as the toolbar") is only true once link
   visibility agrees with the request gate.
3. **1.0.0 released**, so Phase 7 has landed and `docs/development/stability.md` has the provisional tier the new
   names are listed under (navigation decision 5 applied: provisional until the core example and the Tabler theme
   have both rendered it). Building earlier would mean inventing that section and colliding with Phase 7's guard
   test.
4. **The examples restructure merged**, so the dashboard example has a home.

The planning artefact is therefore a GSD phase in the first post-1.0 milestone (GitHub milestone 1.1.0), not a
`superpowers/plans` document: plan 1 core class, tag, leaf, keys, the two `CrudView` attributes and tests; plan 2
docs, example, changelog, stability. The Tabler follow-ups are separate work in `tabler-test`.

## Decisions (maintainer, 2026-11-04)

| # | Question | Decision | Why |
|---|---|---|---|
| 1 | Approach | **A now, C's lazy fetch later**: a request-bound instance of the existing list/card view, framed; the registered-view shape is the from-scratch form and the reserved path for lazy loading. | Every row feature is a view method; B would duplicate them. |
| 2 | Timing | **After 1.0, with all four preconditions** (#311, #312, Phase 7, examples restructure); a GSD phase in milestone 1.1.0; provisional surface. | Same rule as the navigation (decision 5); no stability section invented ahead of Phase 7. |
| 3 | Name | **`DataPanel`**: module `crud_views.lib.datapanel`, tags `cv_datapanel` / `cv_datapanel_for`, keys `datapanel:*`, leaf `tags/datapanel.html`. | Says "a framed box of data" and avoids the clash with Django views. |
| 4 | No access | **Render nothing**; `cv_access` is exposed for a page-side placeholder. No disabled frame, no sixth key. | Nothing to show and nothing to decide about a notice text. |

Calls made in this document that the maintainer did not decide explicitly (correct them if wrong): the "all" link
points at the ViewSet's list page and is on by default; widget links carry no origin (`cv_link_origin`); element ids
get a per-widget prefix (`cv_oid_prefix`, auto `dv<N>` per request); `empty_text` is honoured in both modes through a
guarded line in the stock card content template; `view_attrs` validated like `as_view()` initkwargs; the frame title
is a `level=3` content heading; five class keys with Bootstrap card defaults; `row_actions=False` excludes the
`actions` column / empties `cv_card_actions`.

## Left to the builder

- Module layout inside `crud_views/lib/datapanel.py`, exact exception messages, test names.
- How `mode` detection is implemented (isinstance vs. duck typing on `get_table`).
- Whether `cv_datapanel_for` accepts `key=` as a keyword or a second positional argument.
- The example page's placement in the restructured examples project.
- The German translation of "Show all".
