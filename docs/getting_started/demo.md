# Live demo

The example project runs as a public demo at
**[django-crud-views-demo.onrender.com](https://django-crud-views-demo.onrender.com/)**.

Log in as `alice` / `alice` or `bob` / `bob`. Both have full model permissions in every example. They differ in
the **Guardian** example, which uses per-object permissions: each sees their own documents plus the ones the other
shared with them.

Things to know:

- **The data resets.** Every day at 03:00 UTC, and whenever the demo has been idle for about 15 minutes, it starts
  again from freshly seeded data. Feel free to change and delete things.
- **The first request after a pause can take about a minute** while the free instance wakes up.
- **Saving is rate-limited** to 30 changes per minute and 300 per day per visitor.
- **The Django admin is not available** on the demo.

The demo normally runs the latest release. To run the same project on your machine, see
[Run the finished result first](index.md#or-run-the-finished-result-first).
