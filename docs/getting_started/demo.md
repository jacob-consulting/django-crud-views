# Live demo

The example project runs as a public demo at
**[django-crud-views-demo.onrender.com](https://django-crud-views-demo.onrender.com/)**.

The current example seed provides `alice` / `alice`, `bob` / `bob`, and `developer/developer`.
Developer has read access and developer diagnostics; Alice and Bob have full model permissions in most examples, with these
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

The demo normally runs the latest release; these account instructions describe the current seed, not confirmation
that a hosted deployment has been upgraded. To run the same project on your machine, see
[Run the finished result first](index.md#or-run-the-finished-result-first).

## Developer account and seeded reads

`developer/developer` is a public demo credential, not a production account recipe. The seed creates an active,
nonstaff, nonsuperuser account and adds it to the configured `CRUD_VIEWS_MANAGE_GROUP` (default
`CRUD_VIEWS_MANAGE`). It explicitly grants model reads across the seeded examples, resource `view_s3file`, and
Guardian object reads for Documents, Notes, Projects, Tasks and Milestones. Protected parent Documents also receive
view grants so nested diagnostics can be opened. This grants access to seeded objects; it does not automatically
grant access to future production data. Group membership alone does not bypass ordinary or ancestor permissions.

No add/change/delete or execution permissions are granted to developer. In particular, Contact reminders require
`custom_form.change_contact`, invitations require `custom_form.add_contact`, and the notification composer requires
`flash_messages.add_notice`. Alice and Bob retain those grants. Developer can read the permitted pages and inspect
diagnostics but cannot open or submit these action forms, including the composer. The reusable custom-form classes'
defaults are unchanged; these examples explicitly choose their write permissions.

Fresh and repeated `python manage.py seed` runs create or reuse the accounts, reset demo passwords, and ensure
the configured group, membership and bounded reads without duplicating seed data. Alice/Bob ownership, shares and
restricted scenarios remain intact; neither is automatically added to the manage group. If an existing developer
has conflicting active/staff/superuser flags, direct/group permissions, or object grants on seeded Guardian objects,
or the configured group carries conflicting privileges, the command raises an actionable `CommandError` naming
the conflict. It preserves existing grants rather than silently removing them. Resolve the named account/group
customization deliberately, then rerun the seed; it is not an atomic rollback of earlier seed work.

## Diagnose the signed-in account

Manage pages show current-user permission results for the account signed in. Developer does not impersonate Alice.
To diagnose Alice's results, temporarily add Alice to the configured manage group, sign in as Alice, inspect,
then remove Alice's membership. During that interval Alice herself can open diagnostics.

For your own application, run `python manage.py migrate`, then `python manage.py cv_manage_group` and assign your
chosen active developer users through Django admin or application setup. The command only creates the configured
group; it creates no users and assigns no permissions or memberships. Do not copy the public demo password into
production. No deployed consumer application is automatically upgraded or provisioned by this example seed.
See [manage settings](../reference/settings.md#manage-diagnostics) and the
[migration instructions](../migrating-1.0.md#developer-only-manage-diagnostics).
