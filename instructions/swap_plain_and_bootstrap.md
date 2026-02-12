# Abstract

Currently `djanggo-crud-views` comes with templates that do not require any grid system like Bootstrap.
I call this `plain`.

For a Bootstrap implementation see `crud_views_bootstrap5`. 

Both are django apps.

The installation order of the INSTALLED_APPS is:
- django_crud_views_bootstrap5
- django_crud_views

The reason for this is how Django resolves templates.
It tries to find templates in the INSTALLED_APPS in the order they are listed.

So if a template from `crud_views` is also defined in `crud_views_bootstrap5` which 
is in the first position then this will be used.

This is called template override.

Currently, the `plain` templates defined in `django_crud_views` are the default.

# Tasks

- Make the bootstrap templates (currently in `crud_views_bootstrap5` overriding `django_crud_views`) the default
- So instead of a folder `crud_views_bootstrap5` there will be a folder `crud_views_plain`
- It is important that not all templates in `django_crud_views` also exist in  `crud_views_bootstrap5`
- so all templates that are NOT in `crud_views_bootstrap5` have to be moved from `django_crud_views` to `crud_views_bootstrap5` because this folder will become the new default.
- after the rename of the folder `crud_views_bootstrap5` to `crud_views_plain` the template content can be swapped.
- the same goes for the static folder structure.

- update the documentation
- update tests
- update the demo projects
