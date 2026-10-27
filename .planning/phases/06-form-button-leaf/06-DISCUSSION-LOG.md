# Phase 6: Form-button leaf - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-27
**Phase:** 06-form-button-leaf
**Areas discussed:** Custom filter helpers; custom button templates; which view controls a form.

## Area selection

Offered custom filter helpers, custom button templates, and which view controls a form.
**User choice:** all.

Questions were presented as numbered text because the structured question tool was unavailable in this mode.
The user selected option 1 for every subsequent decision and continuation question.

## Custom filter helpers

### How should existing helpers using add_input(Submit(...)) behave?

| Option | Selected |
|--------|----------|
| Explicit migration (recommended) | Yes |
| Automatic compatibility within the filter integration |  |
| Require migration with a configuration error |  |

**User choice:** 1.

**Captured decision:** Explicit migration: retain existing rendering; document moving buttons into layout FormActions to gain the new leaf, icons and label modes. Hidden sort/order inputs remain on their current path.

### Should legacy placements produce a diagnostic?

| Option | Selected |
|--------|----------|
| Documentation only (recommended) | Yes |
| System-check warning where detectable |  |
| Runtime warning |  |

**User choice:** 1.

**Captured decision:** Documentation only; no new system-check or runtime warnings.

### How should documented field-only subclass layouts work?

| Option | Selected |
|--------|----------|
| Keep it working unchanged (recommended) | Yes |
| Require subclasses to include explicit FormActions |  |

**User choice:** 1.

**Captured decision:** Keep working unchanged: the base helper appends Apply/Reset after the declared fields, exactly once per form.

### How should developers customize default filter controls?

| Option | Selected |
|--------|----------|
| Match existing form hooks (recommended) | Yes |
| Use direct layout editing without a helper hook |  |

**User choice:** 1.

**Captured decision:** Add get_form_actions() to the filter helper, matching CrispyFormMixin, to replace or omit the default actions.

### Next area or more discussion about filter helpers?

| Option | Selected |
|--------|----------|
| Next area: custom button templates | Yes |
| More discussion about filter helpers |  |

**User choice:** 1.

**Captured decision:** Next area: custom button templates.

## Custom button templates

### How should template= work with the new form-button template?

| Option | Selected |
|--------|----------|
| Honor it with the new context (recommended) | Yes |
| Reject explicit overrides; use the shared Django template override |  |

**User choice:** 1.

**Captured decision:** Honor explicit template= with normalized cv_* form-button data and document migration for existing templates.

### Should custom templates also receive crispy's input object?

| Option | Selected |
|--------|----------|
| Only the new cv_* contract (recommended) | Yes |
| Also retain input for compatibility |  |

**User choice:** 1.

**Captured decision:** Only the new cv_* contract; do not expose the legacy input object.

### Should subclass template attributes be supported?

| Option | Selected |
|--------|----------|
| Support both forms (recommended) | Yes |
| Support only template= |  |

**User choice:** 1.

**Captured decision:** Yes. Explicit template= wins, then the subclass template attribute, then the bundled form-button template.

### Should template paths retain crispy's %s template-pack substitution?

| Option | Selected |
|--------|----------|
| Preserve it (recommended) | Yes |
| Require literal paths |  |

**User choice:** 1.

**Captured decision:** Preserve template-pack substitution; custom templates use the new cv_* context.

### Next area or more discussion about custom templates?

| Option | Selected |
|--------|----------|
| Next area: which view controls a form | Yes |
| More discussion about custom templates |  |

**User choice:** 1.

**Captured decision:** Next area: which view controls a form.

## Which view controls a form

### Which view controls form-button label modes when references differ?

| Option | Selected |
|--------|----------|
| Form -> helper -> page (recommended) | Yes |
| Page -> form -> helper |  |
| Reject conflicting views |  |

**User choice:** 1.

**Captured decision:** Form -> helper -> page: prefer form.cv_view, then the helper view, then page-context view. Explicit form ownership wins.

### How should buttons render when there is no crud_views view?

| Option | Selected |
|--------|----------|
| Use project settings and defaults (recommended) | Yes |
| Require a crud_views view |  |

**User choice:** 1.

**Captured decision:** Use the project per-kind form map, then the form label-mode floor; standalone buttons work.

### Does an explicit ordinary Django view stop lookup?

| Option | Selected |
|--------|----------|
| Respect explicit ownership (recommended) | Yes |
| Continue looking for a crud_views view |  |

**User choice:** 1.

**Captured decision:** Yes. Respect explicit ownership and use project settings/defaults, even if the surrounding page has a crud_views view. This qualifies the earlier no-crud-view answer: do not skip an explicit owner to borrow a lower-priority view.

### Should differing view references produce a warning?

| Option | Selected |
|--------|----------|
| No warning (recommended) | Yes |
| Warn on disagreement while using precedence |  |

**User choice:** 1.

**Captured decision:** No warning; differing owners are valid, including embedded forms.

### Finish this area or discuss view resolution further?

| Option | Selected |
|--------|----------|
| Finish this area | Yes |
| Discuss view resolution further |  |

**User choice:** 1.

**Captured decision:** Finish this area and review captured decisions.

## Completion

After reviewing all three areas, the user selected **Ready for context** over **Explore more gray areas**.
This authorized writing the context and discussion log.

## Agent's Discretion

No additional product choice was explicitly delegated. Internal contract organization, exact hook omission
representation, compatibility investigation, test organization, and documentation wording remain research
and implementation work within the captured requirements. These were not presented as user-selected decisions.

## Deferred Ideas

None added; rejected alternatives are recorded above. The required design/spec and dependency verification
remain Phase 6 work. No implementation was performed during this discussion.
