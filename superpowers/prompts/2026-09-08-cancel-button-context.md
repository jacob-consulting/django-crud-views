# New Feature: Cancel Button Context

# Skill
/django-crud-views use it

# Current state
Currently, we can define the cv_cancel_key in a view to specify the context key for the cancel button URL.
That is fine and it works.

# Discussion

The problem is that we cannot use this key to generate the cancel button URL dynamically, depending on the referring view.

For example:
```
list view -> edit -> cancel -> list view
detail view -> edit -> cancel -> detail view
```

I have some ideas, but I don't like them:
- add the referrer view to the generated links
- store in the session the last view key of a viewset visited by the user

# Task

Make three proposals of how to solve this problem.
In the best case the api stays fully backward compatible.

For each proposal, provide a detailed explanation of the proposed solution, including any necessary changes to the existing codebase. 
Additionally, provide a code snippet demonstrating the implementation of the proposed solution.
Add pros/cons for each proposal.

# Constraints
- don't guess
- be precise
- ground everything in existing code
