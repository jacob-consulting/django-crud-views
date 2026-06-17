# Improve Filter

Currently, we have filters for ListView and CardView.
They are not visible by default.
When the user clicks on the filter context button, the the filter is expanded.
The state is stored in the session, if configured.

Our ux department wants to make the filter visible by default.

What it should be:
- configurable state in `ListViewTableFilterMixin`, e.g. `cv_filter_visible_by_default = True`
- the same for `CardListView`
- if the filter is always present
  - the filter context button should be hidden: make a proposal on how to do this
- in both cases the filter settings can be stored in the session

