# Layout Packs

Seven layout packs are included:

| Pack | Setting value |
|------|---------------|
| Split card (default) | `"split-card"` |
| Accordion | `"accordion"` |
| Tabs (vertical) | `"tabs-vertical"` |
| Card rows | `"card-rows"` |
| Striped rows | `"striped-rows"` |
| Table inline | `"table-inline"` |
| List group (3-col) | `"list-group-3col"` |

Set the layout in your Django settings:

```python
CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT = "accordion"
```

## Screenshots

### Split Card (default)

Group title on the left, properties on the right inside a card.

![split-card](screenshots/split-card.png)

### Accordion

Each group is a collapsible accordion panel.

![accordion](screenshots/accordion.png)

### Tabs (vertical)

Groups as vertical tabs with properties in the tab content area.

![tabs-vertical](screenshots/tabs-vertical.png)

### Card Rows

Each group rendered as a standalone card with stacked property rows.

![card-rows](screenshots/card-rows.png)

### Striped Rows

Alternating row backgrounds for easy scanning.

![striped-rows](screenshots/striped-rows.png)

### Table Inline

Classic table layout with label and value columns.

![table-inline](screenshots/table-inline.png)

### List Group (3-col)

Three-column list group with label, value, and detail.

![list-group-3col](screenshots/list-group-3col.png)
