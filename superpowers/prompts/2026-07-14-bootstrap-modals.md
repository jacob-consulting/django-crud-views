# New Feature: Modals

I want to plan a new feature for django-crud-views: Modal windows.
For now this will be implemented only with Bootstrap.

# Skill
/django-crud-views use it

# Discussion

Currently, we have confirmation pages for delete.
These do a check if the object can be deleted.
If it can, a delete button is shown, which posts to the delete view, which does the action.
After that the user is redirected to the list view, or something else depending on the view's configuration.

My idea for this:
- introduce a cv_modal:bool option for views
- currently I see there:
  - delete
  - custom form view
  - detail view
- I am not sure about, needs discussion:
  - create
  - update

For now only for bootstrap5.

Elaborate multiple solutions for this new feature in the brainstorming session.
The result should not be an implementation, but rather one Markdown document
which describes the different solutions in details with pros/cons and code examples.

This document will be the input for the final brainstorming session for the implementation.

# Constraints
- don't guess
- be precise
- ground everything in existing code
