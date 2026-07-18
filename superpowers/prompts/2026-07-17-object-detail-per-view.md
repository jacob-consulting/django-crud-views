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
- as an app in `src/crud_views_object_detail`

# implementation
- instead of the adapter, object-detail it would be nativly integrated 

# documentation
- integrate django-object-detail documentation into django-crud-views
- update the existing documentation about detail views

# examples
- add an example app 
- with a nav item
- and a badge on the index page
- the viewset has one detail view per object-detail theme, so all themes are available in the examples
- the app's model for that should have some data types that show how object details renders them by default
  - boolean
  - date
  - datetime
  - TODO: extend the list
- also showcase features:
  - access nested objects -> second model in the app
  - access properties/functions from the view/model  
- evaluate the example app in django-object-detail
  - all important features/showcases must make it into our examples
  
# django-object-detail
- after integration, update the project's README.md, explain that is integrated in django-crud-views now
- set the project to archive

# judgement

Is this a good idea? Be honest, list pros/cons.