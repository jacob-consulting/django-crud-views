The django-polymorphic implementation in [crud_views](../crud_views) is located in [polymorphic_views](../polymorphic_views).
In crud_views I don't want to have a requirement to install django-polymorphic.

- Therefore, add a package `crud_views_polymorphic` to the project.
- do it similar to `crud_views_workflow`
- move the polymorphic views to the new package
- update examples
- update tests
- update documentation
