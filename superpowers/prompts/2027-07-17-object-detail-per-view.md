# integrate django-object-detail

django-object-detail is an extra repository also available in pypi.
It is locally checked out at `../django-object-detail`

# current status
- it has been developed to be used in conjunction with django-crud-views
- I have not touched the package since its last release
- for django-crud-views I had to write an adapter so it works in the detail view
- django-object-detail documentation is already partially cloned in django-crud-views documentation

# idea
- integrate django-object-detail into django-crud-views
- not sure how:
  - as an app in `src/django_object_detail`, but better renamed as `src/crud_views_object_detail`
  - or directly in crud_views
  - list pros/cons

# documentation
- integrate django-object-detail documentation into django-crud-views

# examples
- add an example where the viewset hast one detail view per theme, so all themes available in the examples

# django-object-detail
- after integration, update the project's README.md, explain that is integrated in django-crud-views now
- set the project to archived
