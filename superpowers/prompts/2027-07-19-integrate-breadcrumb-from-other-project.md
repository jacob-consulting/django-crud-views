# Integrate breadcrumb from another project

> IMPORTANT: do not commit literals `***` or `***`, `***` or similar, 
> because these names from the project source MUST NOT appear in this public rep.
> We do not need to check in spec/plan, so we are sure to do so.
> So you can reference these in plan/spec, but never commit them.
> Also never reference them in commits of the new feature.

# git-worktree
Use a git worktree for this feature. another session is working on the project.

# Abstract
In the project `../../***-examples` I have a draft of a breadcrumb component, 
that I want to integrate in django-crud-views.

# Tasks
- we have `Breadcrumb`, and `BreadcrumbItem`, these are dataclass based, but we have pydantic as standard
- also there is `***CrudViewMenuMixin`, we should rename it to `CrudViewBreadcrumbMixin` because it is not really a menu
- the code to determine the breadcrumb hierarchy is a sort of a prototype,
  - analyze this in detail if it is working in all known use cases
  - does this have any weaknesses?
  - performance issues?
  - security issues?
  - the result must be production grade in all these aspects
- Hookable into an existing project navigation
  - this feature is not a navigation feature
  - it is just for the breadcrumb part that within django-crud-views hierarchy
  - as you can see, the source project hard-codes an external navigation prefix to the chain
    - this must be planned and configurable
- for the templates use https://getbootstrap.com/docs/5.3/components/breadcrumb/
  - we are already using bootstrap 5
- update example app
  - all viewset should use it
  - one extra example app that shows how to inject at min to parent breadcrumb items, simulating  an integration in another project
  - also with code explanation, and what it show text
- tests
  - for the new module
  - and for the example app
- documentation
  - for the new module
  - faq
- update skill
 