# Cycle 4 supplementary probes

Executed /tmp/review062-cycle4-probe.py in separate processes under cached Django 4.2.30 and 6.0.9 interpreters. Repository files were not modified. The process inserted a prototype cooperative guard after CrudView/before Django DeleteView into the existing class bases and filtered DELETE from _allowed_methods. All other method names remained inherited, including delete; therefore this exercises the restored-name case.

Both returned DELETE 405, OPTIONS 200, matching Allow GET/POST/OPTIONS (no DELETE), Vary X-CV-Modal, unchanged DeletionMixin.delete identity, and no DeleteViewCustomDeleteWarning. Actual Guardian MRO placed GuardianParentPermissionMixin and PermissionRequiredMixin before CrudView, followed by the guard and Django DeleteView. This is a mechanism probe, not execution of the planned implementation or full authorization/POST suites.

Annotation-only declarations on GuardianParentPermissionMixin preserved inherited global=True/anonymous=404 in separate composed custom object and queryset mixins in both environments.

Exit code 0 for each process. No new tests were written to the repository; full future regression evidence remains owned by execution.
