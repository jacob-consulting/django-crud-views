from crud_views.lib.conditional import QuerysetConditions

SERVICE_CONDITIONS = QuerysetConditions(
    "service",
    conditional_key="conditional_category",
    keys=("on_site", "remote", "general"),
)
VISIT_CONDITION = SERVICE_CONDITIONS.when("on_site")
REMOTE_CONDITION = SERVICE_CONDITIONS.when("remote")
# General is declared above and deliberately belongs to neither field group.
