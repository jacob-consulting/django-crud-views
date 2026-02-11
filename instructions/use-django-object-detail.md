# Abstract

The django-crud-views project has a detail view defined in `crud_views/lib/views/detail.py`

This functionality can add groups and properties to display in the detail view.

# Current state
More detail view code is here:
- `crud_views/lib/views/properties`
- `crud_views/lib/views/properties`
- `crud_views/templates/crud_views/tabs`
- `crud_views/templates/crud_views/properties`

# Task
I want to replace the functionality in the detail view with this package: 
- https://pypi.org/project/django-object-detail/
- the code can be found locally here `/home/alex/projects/playground/claude/django-object-view`
- the local code also contains the documentation

The functionality is basically the same, so do the following:

- add `django-object-detail` to `pyproject.toml`
- replace old code by using `django-object-detail`
- also replace existing code in `crud_views/examples/bootstrap`
- do not touch `crud_views/examples/`plain, this will be in a separate task
- add feature to CHANGELOG.md
- update the list of projects that django-crud-views uses in README.md and the documentation
