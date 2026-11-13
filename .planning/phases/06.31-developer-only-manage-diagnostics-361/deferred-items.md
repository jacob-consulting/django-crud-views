# Deferred items

## Pre-existing invitation success-message wording (06.31-04)

- A successful POST to `contact-invite` creates the Contact and emits a success message, but the message reads
  `Invited “”` rather than including the email. Observed while exercising seeded Alice/Bob in
  `ContactSeedPermissionsTest.test_repeated_seed_preserves_demo_user_permissions_and_actions`.
- `ContactInviteView.cv_message_template_code` references `form.cleaned_data.email`; the existing
  `MessageMixin.cv_form_valid_hook` calls `cv_get_message()` without the validated form context. Neither path
  is changed by this plan's permission declarations.
- Kept out of the authorization fix. The positive regression verifies row creation and the success-message
  level; denied requests verify that no message is emitted. A future message-context task can correct the text.
