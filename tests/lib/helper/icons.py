"""A host-placement icon library (#258) and an icon table that maps a few semantic names to it."""

HOST_LIBRARY = {
    "ui": {"renderer": "font", "class": "icon-{name}", "placement": "host", "standalone": "icon {name_class}"},
}

HOST_ICONS = {
    "detail": "ui:eye",
    "update": "ui:edit",
    "actions-menu": "ui:dots",
    "filter": "ui:funnel",
    "filter-close": "ui:x",
}
