# Review request: DataPanel design and its prerequisites (#311, #312)

## Your role

You are a fresh, critical reviewer of django-crud-views. You have not seen these documents before and you
cannot ask me questions. Judge hard, be honest, and never guess: every claim you make must point at a file and
line in this repository, at a cited document, or at a test you actually ran. If you cannot verify something, say
so instead of filling the gap.

Do not rewrite the design and do not implement anything. The deliverable is a written review.

## What to read, in this order

1. `CLAUDE.md` and `AGENTS.md` (project conventions), `docs/development/stability.md` (what the 1.0 contract
   protects), `docs/reference/theme.md` (theming rules: hooks before overrides, "hiding is presentation") and
   `docs/reference/nested.md`.
2. `superpowers/notes/2026-11-02-navigation-concept-exploration.md` on `main`: its decisions table (§7) and the
   implementer brief (§9) are the origin of the two prerequisite issues and of several rules the DataPanel design
   reuses (visibility rule, provisional surface, "fix the two `cv_has_access` gaps first").
3. The two documents under review, on branch `claude/lucid-knuth-x5ity9`:
   - `superpowers/notes/2026-11-04-dataview-concept-exploration.md` (research, approaches A/B/C; working name
     DataView)
   - `superpowers/specs/2026-11-04-datapanel-design.md` (the chosen design; its "Decisions" section lists what I
     decided and what the author decided for me)
4. GitHub issues #311 and #312 in `jacob-consulting/django-crud-views`, the prerequisites of the design.
5. The phase currently implementing those issues:
   `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity` (CONTEXT, RESEARCH, PLANs and
   whatever else is there), plus the code on its branch if it exists.
6. The real downstream consumer, the sibling checkout `../tabler-test`: `example/dashboard/` (the two hand-written
   widgets the design is meant to replace), `src/crud_views_tabler/` (the theme), and
   `docs/crud_views_upstream_findings_roastery.md` (finding 27 and anything about nested links or dashboards).

## Part 1: the DataPanel design

Answer each question with a verdict (yes / no / partly) and the evidence.

1. **Is it a good design?** Does it solve the stated intent (several fixed-size, unordered lists of crud objects on
   a non-crud page, with the crud-views links, actions, permissions and theme), and nothing beyond it?
2. **Is it durable?** Which parts depend on internals that are likely to change (`View.setup` binding, instance
   attributes like `paginate_by` / `table_pagination` / `cv_order_fields`, the `cv_content_template` partials,
   `get_table` kwargs, `cv_get_oid`)? Would a plausible future change to list or card views silently break it?
3. **Is it useful for other future work?** Check specifically against the navigation design on `main` (shared
   visibility rule, request-free URL needs, lazy-load path) and against tabler-test's dashboard. Would a theme
   author or a project author reach for it, or work around it?
4. **Will the code be easy to understand?** Judge the proposed API (constructor options, `from_viewset`,
   `view_attrs`, the two from-scratch shapes, `cv_link_origin`, `cv_oid_prefix`) for surprise, for hidden
   coupling, and for how a reader of a dashboard view would follow what happens at render time.
5. **Challenge the calls** listed in the spec's "Decisions" section one by one. For each: keep, change, or needs a
   decision I have not seen. Say which.
6. **Verify the claims** the design rests on by reading the code, and run anything cheap that settles a doubt
   (e.g. a `RequestFactory`-bound `ListView` instance with the proposed attribute overrides; whether a sliced
   queryset survives django-tables2 with `orderable=False`; what `cv_card` needs in context). Report what you ran.
7. **What would you change before anyone plans this?** Rank by impact.

## Part 2: the prerequisites #311 and #312

1. Are the two issues correct about the code today? Re-check every line reference and every "behaviour today"
   claim against the current tree.
2. Is the proposed change in each issue the right one? Consider the alternatives the issue dismisses and any it
   does not mention.
3. Are they really prerequisites of the DataPanel design, and in the order stated (helper, then 311's builders,
   then 312)? Could the design ship without either, and what would break?
4. The core parent-permission gap noted in #311: is the note accurate, and is "out of scope, follow-up" the
   right call, or does the DataPanel design depend on resolving it?

## Part 3: the phase 06.10 artefacts

1. Does the phase implement what the issues say? List every deviation and say whether it is an improvement, a
   loss, or neutral.
2. Did I make the right decisions in that phase (the D-nn entries)? For each one you disagree with: why, with
   evidence, and what you would decide instead.
3. Flaws: anything that would make link visibility and the request gate disagree again, any new query cost
   without a pinned count, any public name added without a stability entry, any test that cannot catch the
   regression it is for.
4. If code exists on the phase branch, run its tests and the full suite (`pytest tests -n auto`) and report
   results.

## Output

Write the review to `superpowers/notes/<today>-datapanel-and-prerequisites-review.md` on the branch you are
working from and give me the path. Structure it as the three parts above. Lead each part with a one-paragraph
verdict, then ranked findings. Each finding: what, where (`file:line` or document section), why it matters, what
you recommend. Separate "verified" from "could not verify". Keep opinions out of the findings; put them in a
short closing section titled "If this were mine".
