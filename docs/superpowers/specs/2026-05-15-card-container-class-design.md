# Design: Configurable Card Container Class

## Problem

The card grid template (`view_card.content.html`) hardcodes `col-md-6` on the container wrapping each card. Users cannot control the card width without overriding the entire template.

## Solution

Add a `cv_card_container_class` class attribute to `CardListView` with a default of `"col-md-6"`. The template reads it via `{{ view.cv_card_container_class }}`.

## Changes

### 1. `crud_views/lib/views/card.py`

Add `cv_card_container_class: str = "col-md-6"` to `CardListView`, alongside the existing `cv_card_template` and `cv_card_actions` attributes.

### 2. `crud_views/templates/crud_views/view_card.content.html`

Replace the hardcoded `<div class="col-md-6">` with `<div class="{{ view.cv_card_container_class }}">`.

### 3. `docs/reference/card-list-view.md`

Add a "Card Container Class" section documenting the property with a usage example showing `col-md-12` for full-width cards.

### 4. `skills/django-crud-views/SKILL.md`

Mention `cv_card_container_class` in the CardListView section.

### 5. `tests/test1/test_card.py`

- Test that the default container class renders `col-md-6` on card wrapper divs.
- Test that a custom container class (e.g., `col-md-12`) renders correctly when overridden.

## Scope

- Bootstrap 5 theme only (plain theme unchanged).
- No changes to `CardAction`, template tags, `get_context_data`, or base view.
