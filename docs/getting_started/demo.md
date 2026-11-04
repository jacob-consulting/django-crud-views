# Live demo

The example project runs as a public demo at
**[django-crud-views-demo.onrender.com](https://django-crud-views-demo.onrender.com/)**.

Log in as `alice` / `alice` or `bob` / `bob`. Both have full model permissions in most examples, with these
differences:

- **Library** gives Alice view permission for Ursula Le Guin's `Earthsea publishing contract`; its permitted
  label is plain text on the blocked delete page or modal. Bob sees a generic blocked notice without its label.
  Neither can delete Ursula. Other authors demonstrate Book cascades: Book links open ordinary full pages,
  including from a delete modal. The Contract detail view is separately available to Alice; neither account
  gets Contract add/change/delete permissions.
- **Context Buttons** and **Action Menus**, where bob may only view, to show what a restricted user sees: actions he
  may not use disappear, or, in Action Menus, show disabled ("Archive").
- **Guardian**, which uses per-object permissions: each user sees their own documents plus the ones the other shared
  with them.
- **Delete**, which also uses per-object permissions: each user sees their own projects and tasks. One of alice's
  projects is blocked by a task of bob's that she cannot see. Permitted protected Task labels are plain text.

Delete previews default to **50** displayed objects shared across protected labels and cascade entries.
An explicit `cv_delete_preview_limit = None` shows all visible entries, which can produce long pages and
more optional cascade-link work. Neither policy limits complete inspection or visibility filtering, nor
changes deletion protection. See [DeleteView](../reference/delete_view.md#cascading-deletes-display).

Things to know:

- **The data resets.** Every day at 03:00 UTC, and whenever the demo has been idle for about 15 minutes, it starts
  again from freshly seeded data. Feel free to change and delete things.
- **The first request after a pause can take about a minute** while the free instance wakes up.
- **Saving is rate-limited** to 30 changes per minute and 300 per day per visitor.
- **The Django admin is not available** on the demo.

The demo normally runs the latest release. To run the same project on your machine, see
[Run the finished result first](index.md#or-run-the-finished-result-first).
