"""
Tests for crud_views_workflow: WorkflowModelMixin, WorkflowView, WorkflowForm.
"""

import pytest
from django.contrib.messages import get_messages
from django.test import override_settings
from django.test.client import Client

from crud_views.lib import button_classes as bc
from crud_views_workflow.lib.enums import BadgeEnum
from crud_views_workflow.models import WorkflowInfo
from tests.test1.app.models import Campaign, CampaignState


@pytest.fixture
def badge_registry():
    saved = bc._THEME_BUTTON_CLASSES.copy()
    try:
        yield
    finally:
        bc._THEME_BUTTON_CLASSES.clear()
        bc._THEME_BUTTON_CLASSES.update(saved)
        bc.reset_button_classes_cache()


@pytest.mark.django_db
def test_workflow_badge_registry_request_tracer(client_user_campaign_change, campaign_new, badge_registry):
    bc.register_button_classes({"workflow:badge-light": "theme-old", "workflow:badge-info": "theme-current"})
    url = f"/campaign/{campaign_new.pk}/workflow/"
    response = client_user_campaign_change.post(url, {"transition": "wf_activate", "comment": ""})
    assert response.status_code == 302
    campaign_new.refresh_from_db()
    assert campaign_new.state == CampaignState.ACTIVE
    assert WorkflowInfo.objects.filter(workflow_object_pk=str(campaign_new.pk)).count() == 1
    response = client_user_campaign_change.get(url)
    assert response.status_code == 200
    assert '<span class="theme-old">New</span>' in response.content.decode()
    assert '<span class="theme-current">Active</span>' in response.content.decode()
    assert campaign_new.state_badge == '<span class="theme-current">Active</span>'
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"workflow:badge-info": "project-current"}):
        assert campaign_new.state_badge == '<span class="project-current">Active</span>'
        campaign_new.STATE_BADGES = {}
        assert campaign_new.get_state_badge(CampaignState.ERROR) == '<span class="project-current">Error</span>'


@pytest.mark.parametrize("colour", list(BadgeEnum))
def test_workflow_badge_stock_colours(colour):
    campaign = Campaign(state=CampaignState.NEW)
    campaign.STATE_BADGES = {CampaignState.NEW: colour}
    assert campaign.state_badge == f'<span class="badge rounded-pill text-bg-{colour}">New</span>'


@pytest.mark.django_db
@pytest.mark.parametrize("colour", ["info", "purple"])
@pytest.mark.parametrize("source", ["theme", "settings"])
@pytest.mark.parametrize("value", ["missing", None, "", " custom  complete-classes "])
def test_workflow_badge_registry_edges(
    client_user_campaign_change, campaign_new, badge_registry, colour, source, value
):
    key = f"workflow:badge-{colour}"
    classes = {} if value == "missing" else {key: value}
    if source == "theme":
        bc.register_button_classes(classes)
        project = {}
    else:
        if classes:
            bc.register_button_classes({key: "losing-theme-classes"})
        project = classes
    url = f"/campaign/{campaign_new.pk}/workflow/"
    assert client_user_campaign_change.post(url, {"transition": "wf_activate", "comment": ""}).status_code == 302
    campaign_new.refresh_from_db()
    campaign_new.STATE_BADGES = {CampaignState.NEW: colour, CampaignState.ACTIVE: colour}
    expected = f"badge rounded-pill text-bg-{colour}" if value == "missing" else value or ""
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=project):
        assert campaign_new.state_badge == f'<span class="{expected}">Active</span>'
        (history,) = campaign_new.workflow_data
        assert history["state_old_badge"] == f'<span class="{expected}">New</span>'
        assert history["state_new_badge"] == f'<span class="{expected}">Active</span>'
        # A missing model mapping chooses STATE_BADGE_DEFAULT, not the last custom colour.
        campaign_new.STATE_BADGES = {}
        campaign_new.STATE_BADGE_DEFAULT = BadgeEnum.DANGER
        assert campaign_new.state_badge == '<span class="badge rounded-pill text-bg-danger">Active</span>'


def test_workflow_badge_legacy_override_context(badge_registry):
    from django.template.loader import render_to_string

    from tests.test1.test_form_frame import _theme_templates

    campaign = Campaign(state=CampaignState.NEW)
    bc.register_button_classes({"workflow:badge-light": "new-classes"})
    path = "crud_views_workflow/badge.html"
    legacy = '<span data-state="{{ state }}" class="old-{{ class }}">{{ name }}</span>'
    with _theme_templates({path: legacy}):
        assert campaign.state_badge == '<span data-state="new" class="old-light">New</span>'
    assert render_to_string(path, {"state": "new", "name": "Old caller", "class": "purple"}) == (
        '<span class="badge rounded-pill text-bg-purple">Old caller</span>'
    )
    assert campaign.state_badge == '<span class="new-classes">New</span>'


@pytest.mark.django_db
@pytest.mark.parametrize("input_kind", ["label", "colour", "classes"])
@pytest.mark.parametrize("source", ["theme", "settings"])
def test_workflow_badge_escaping(
    client_user_campaign_change, campaign_new, badge_registry, monkeypatch, input_kind, source
):
    from django.utils.html import escape
    from lxml import html

    hostile = '"><svg onload="bad()">& {{ 7|add:7 }} {% cycle "x" "y" %}'
    url = f"/campaign/{campaign_new.pk}/workflow/"
    assert client_user_campaign_change.post(url, {"transition": "wf_activate", "comment": ""}).status_code == 302
    campaign_new.refresh_from_db()
    colour = hostile if input_kind == "colour" else "purple"
    campaign_new.STATE_BADGES = {CampaignState.NEW: colour, CampaignState.ACTIVE: colour}
    if input_kind == "label":
        monkeypatch.setattr(campaign_new, "get_state_name", lambda state: hostile)
    classes = {"workflow:badge-purple": hostile} if input_kind == "classes" else {}
    if source == "theme":
        bc.register_button_classes(classes)
        classes = {}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=classes):
        (history,) = campaign_new.workflow_data
        rendered = [campaign_new.state_badge, history["state_old_badge"], history["state_new_badge"]]
    for badge in rendered:
        assert str(escape(hostile)) in badge
        node = html.fromstring(badge)
        assert node.tag == "span"
        assert list(node) == []
        assert set(node.attrib) == {"class"}
        expected_class = hostile if input_kind == "classes" else f"badge rounded-pill text-bg-{colour}"
        assert node.get("class") == expected_class
        if input_kind == "label":
            assert node.text == hostile


# ---------------------------------------------------------------------------
# WorkflowModelMixin model-layer tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("entries", [0, 1, 2])
def test_workflow_history_presentation(client_user_campaign_change, campaign_new, entries, monkeypatch):
    from lxml import html

    from tests.test1.test_form_frame import THEME_FRAME, _theme_templates
    from tests.test1.test_theme_form_ownership import _RawForms

    url = f"/campaign/{campaign_new.pk}/workflow/"
    hostile = '<script>alert("history")</script>& {{ 7|add:7 }}'
    for transition in ("wf_activate", "wf_done")[:entries]:
        response = client_user_campaign_change.post(url, {"transition": transition, "comment": hostile})
        assert response.status_code == 302
    monkeypatch.setattr(Campaign, "get_state_name", lambda self, state: hostile + state)
    with _theme_templates({"crud_views/snippets/form_frame.html": THEME_FRAME}):
        response = client_user_campaign_change.get(url)
    assert response.status_code == 200
    scanner = _RawForms()
    scanner.feed(response.content.decode())
    assert not scanner.stack
    document = html.fromstring(response.content)
    (frame,) = document.cssselect(".theme-card")
    headings = document.xpath("//h5[normalize-space()='Workflow History']")
    if not entries:
        assert not headings
        assert not document.cssselect(".table-responsive, table")
        assert frame.cssselect("form.cv-form")
        return
    (heading,) = headings
    wrapper = heading.getnext()
    assert wrapper.tag == "div"
    assert wrapper.get("class") == "table-responsive"
    (table,) = list(wrapper)
    assert table.tag == "table" and table.get("class") == "table"
    assert wrapper.getnext() is frame
    assert heading.getparent() is wrapper.getparent() is frame.getparent()
    assert len(table.cssselect("thead th[scope=col]")) == 6
    assert len(table.cssselect("tbody tr")) == entries
    assert not table.cssselect("script, svg")
    for row in table.cssselect("tbody tr"):
        assert len(row) == 6
        assert row[2].cssselect("span")[0].text.startswith(hostile)
        assert row[3].cssselect("span")[0].text.startswith(hostile)
    # The optional comment on Done is persisted; Activate deliberately ignores comments.
    if entries == 2:
        assert table.cssselect("tbody tr")[-1][4].text_content().strip() == hostile
        assert not frame.cssselect("form, input, button, h5")
    else:
        assert frame.cssselect("form.cv-form")


@pytest.mark.parametrize("source", ["theme", "settings"])
@pytest.mark.parametrize("wrapper_class", ["default", 'custom-wrapper" onclick="bad()', "", None])
@pytest.mark.parametrize("table_class", ["default", 'custom-table" onclick="bad()', "", None])
def test_workflow_history_presentation_classes(badge_registry, source, wrapper_class, table_class):
    from django.template.loader import render_to_string
    from lxml import html

    classes = {
        key: value
        for key, value in (("workflow:history-wrapper", wrapper_class), ("workflow:history-table", table_class))
        if value != "default"
    }
    if source == "theme":
        bc.register_button_classes(classes)
        project = {}
    else:
        bc.register_button_classes(dict.fromkeys(classes, "losing-theme-class"))
        project = classes
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=project):
        markup = render_to_string(
            "crud_views_workflow/view_workflow.history.html",
            {"object": {"workflow_data": [{"comment": "Preserved history"}]}},
        )
    root = html.fragment_fromstring(markup, create_parent="div")
    heading, wrapper = list(root)
    assert heading.text_content() == "Workflow History"
    assert wrapper.tag == "div"
    (table,) = list(wrapper)
    assert table.tag == "table"
    assert set(wrapper.attrib) == set(table.attrib) == {"class"}
    assert wrapper.get("class", "") == ("table-responsive" if wrapper_class == "default" else wrapper_class or "")
    assert table.get("class", "") == ("table" if table_class == "default" else table_class or "")
    assert len(table.cssselect("thead th[scope=col]")) == 6
    assert table.cssselect("tbody tr td")[4].text_content().strip() == "Preserved history"


@pytest.mark.django_db
def test_state_name_new(campaign_new):
    assert campaign_new.state_name == "New"


@pytest.mark.django_db
def test_state_name_active(campaign_active):
    assert campaign_active.state_name == "Active"


@pytest.mark.django_db
def test_state_name_success(campaign_success):
    assert campaign_success.state_name == "Success"


@pytest.mark.django_db
def test_get_state_name(campaign_new):
    assert campaign_new.get_state_name(CampaignState.NEW) == "New"
    assert campaign_new.get_state_name(CampaignState.ACTIVE) == "Active"
    assert campaign_new.get_state_name(CampaignState.SUCCESS) == "Success"
    assert campaign_new.get_state_name(CampaignState.CANCELED) == "Cancelled"


@pytest.mark.django_db
def test_state_badge_new(campaign_new):
    badge = campaign_new.state_badge
    assert "New" in badge
    assert "badge" in badge
    assert "light" in badge  # STATE_BADGES[NEW] = BadgeEnum.LIGHT


@pytest.mark.django_db
def test_get_state_badge_active(campaign_new):
    badge = campaign_new.get_state_badge(CampaignState.ACTIVE)
    assert "Active" in badge
    assert "info" in badge  # STATE_BADGES[ACTIVE] = BadgeEnum.INFO


@pytest.mark.django_db
def test_get_state_badge_unknown_uses_default(campaign_new):
    # State not in STATE_BADGES falls back to STATE_BADGE_DEFAULT badge class
    campaign_new.STATE_BADGES = {CampaignState.NEW: BadgeEnum.LIGHT}  # ERROR intentionally missing
    result = campaign_new.get_state_badge(CampaignState.ERROR)
    assert "Error" in result
    assert "badge" in result  # still renders a badge, not plain text
    assert "info" in result  # STATE_BADGE_DEFAULT = BadgeEnum.INFO


@pytest.mark.django_db
def test_workflow_possible_transitions_new(campaign_new, user_campaign_change):
    transitions = campaign_new.workflow_get_possible_transitions(user_campaign_change)
    names = [t[0] for t in transitions]
    assert "wf_activate" in names
    assert "wf_cancel_new" in names
    # wf_done is only available from ACTIVE
    assert "wf_done" not in names


@pytest.mark.django_db
def test_workflow_possible_transitions_active(campaign_active, user_campaign_change):
    transitions = campaign_active.workflow_get_possible_transitions(user_campaign_change)
    names = [t[0] for t in transitions]
    assert "wf_done" in names
    assert "wf_cancel_active" in names
    # wf_activate is only available from NEW
    assert "wf_activate" not in names


@pytest.mark.django_db
def test_workflow_possible_transitions_success_empty(campaign_success, user_campaign_change):
    transitions = campaign_success.workflow_get_possible_transitions(user_campaign_change)
    assert transitions == []


@pytest.mark.django_db
def test_workflow_has_transition_true(campaign_new, user_campaign_change):
    assert campaign_new.workflow_has_transition(user_campaign_change, "wf_activate") is True


@pytest.mark.django_db
def test_workflow_has_transition_false_wrong_state(campaign_new, user_campaign_change):
    # wf_done requires ACTIVE state
    assert campaign_new.workflow_has_transition(user_campaign_change, "wf_done") is False


@pytest.mark.django_db
def test_workflow_has_any_transition_true(campaign_new, user_campaign_change):
    assert campaign_new.workflow_has_any_possible_transition(user_campaign_change) is True


@pytest.mark.django_db
def test_workflow_has_any_transition_false_terminal(campaign_success, user_campaign_change):
    assert campaign_success.workflow_has_any_possible_transition(user_campaign_change) is False


@pytest.mark.django_db
def test_workflow_comment_kwargs_with_comment():
    result = Campaign.workflow_comment_kwargs("hello")
    assert result == {"comment": "hello"}


@pytest.mark.django_db
def test_workflow_comment_kwargs_without_comment():
    result = Campaign.workflow_comment_kwargs(None)
    assert result == {}


@pytest.mark.django_db
def test_workflow_comment_kwargs_empty_string():
    result = Campaign.workflow_comment_kwargs("")
    assert result == {}


@pytest.mark.django_db
def test_workflow_data_empty(campaign_new):
    assert campaign_new.workflow_data == []


@pytest.mark.django_db
def test_workflow_transition_label_map(campaign_new):
    label_map = campaign_new.workflow_get_transition_label_map
    assert "wf_activate" in label_map
    assert label_map["wf_activate"] == "Activate"
    assert "wf_done" in label_map
    assert label_map["wf_done"] == "Done"
    assert "wf_cancel_new" in label_map
    assert label_map["wf_cancel_new"] == "Cancel"


@pytest.mark.django_db
def test_workflow_get_transition_label(campaign_new):
    assert campaign_new.workflow_get_transition_label("wf_activate") == "Activate"
    assert campaign_new.workflow_get_transition_label("wf_done") == "Done"


@pytest.mark.django_db
def test_workflow_get_form_kwargs(campaign_new, user_campaign_change):
    kwargs = campaign_new.workflow_get_form_kwargs(user_campaign_change)
    assert "choices" in kwargs
    assert "transition_comments" in kwargs
    choice_names = [c[0] for c in kwargs["choices"]]
    assert "wf_activate" in choice_names
    assert "wf_cancel_new" in choice_names


@pytest.mark.django_db
def test_workflow_get_form_kwargs_labels(campaign_new, user_campaign_change):
    kwargs = campaign_new.workflow_get_form_kwargs(user_campaign_change)
    choices_dict = dict(kwargs["choices"])
    assert choices_dict["wf_activate"] == "Activate"
    assert choices_dict["wf_cancel_new"] == "Cancel"


@pytest.mark.django_db
def test_workflow_get_form_kwargs_comment_types(campaign_new, user_campaign_change):
    from crud_views_workflow.lib.enums import WorkflowComment

    kwargs = campaign_new.workflow_get_form_kwargs(user_campaign_change)
    tc = kwargs["transition_comments"]
    assert tc["wf_activate"] == WorkflowComment.NONE
    assert tc["wf_cancel_new"] == WorkflowComment.REQUIRED


def test_comment_default_is_none():
    """COMMENT_DEFAULT defaults to WorkflowComment.NONE."""
    from crud_views_workflow.lib.enums import WorkflowComment
    from crud_views_workflow.lib.mixins import WorkflowModelMixin

    assert WorkflowModelMixin.COMMENT_DEFAULT == WorkflowComment.NONE


@pytest.mark.django_db
def test_comment_default_fallback(campaign_new, user_campaign_change):
    """COMMENT_DEFAULT is used when a transition omits 'comment' from custom."""
    from unittest.mock import MagicMock, patch

    from crud_views_workflow.lib.enums import WorkflowComment

    mock_transition = MagicMock()
    mock_transition.name = "wf_test"
    mock_transition.custom = {"label": "Test"}  # no 'comment' key

    with patch.object(campaign_new, "get_available_user_state_transitions", return_value=[mock_transition]):
        transitions = campaign_new.workflow_get_possible_transitions(user_campaign_change)
        assert transitions[0][2] == WorkflowComment.NONE  # default


@pytest.mark.django_db
def test_comment_default_override(campaign_new, user_campaign_change):
    """Overriding COMMENT_DEFAULT changes the fallback for transitions without an explicit comment."""
    from unittest.mock import MagicMock, patch

    from crud_views_workflow.lib.enums import WorkflowComment

    mock_transition = MagicMock()
    mock_transition.name = "wf_test"
    mock_transition.custom = {"label": "Test"}  # no 'comment' key

    campaign_new.COMMENT_DEFAULT = WorkflowComment.OPTIONAL
    with patch.object(campaign_new, "get_available_user_state_transitions", return_value=[mock_transition]):
        transitions = campaign_new.workflow_get_possible_transitions(user_campaign_change)
        assert transitions[0][2] == WorkflowComment.OPTIONAL


# ---------------------------------------------------------------------------
# WorkflowView HTTP tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_workflow_view_get(client_user_campaign_change: Client, campaign_new):
    response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_workflow_view_get_shows_transitions(client_user_campaign_change: Client, campaign_new):
    response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/")
    assert response.status_code == 200
    assert response.context["has_workflow_choices"] is True


@pytest.mark.django_db
def test_workflow_view_get_terminal_state_no_choices(client_user_campaign_change: Client, campaign_success):
    response = client_user_campaign_change.get(f"/campaign/{campaign_success.pk}/workflow/")
    assert response.status_code == 200
    assert response.context["has_workflow_choices"] is False


@pytest.mark.django_db
def test_workflow_view_post_activate(client_user_campaign_change: Client, campaign_new):
    pk = campaign_new.pk
    response = client_user_campaign_change.post(
        f"/campaign/{pk}/workflow/",
        {
            "transition": "wf_activate",
            "comment": "",
        },
    )
    assert response.status_code == 302
    campaign_new.refresh_from_db()
    assert campaign_new.state == CampaignState.ACTIVE


@pytest.mark.django_db
def test_workflow_view_post_emits_success_message(client_user_campaign_change: Client, campaign_new):
    """
    A WorkflowView that mixes in MessageMixin (as CampaignWorkflowView does) emits its
    configured success message after a transition. MessageMixin's cv_form_valid_hook runs
    after WorkflowView.cv_form_valid has processed the transition, then emits the message.
    Regression guard for GitHub #52 (reported as "message never emitted" — it is emitted under
    the documented MessageMixin opt-in, exactly like Create/Update/Delete views).
    """
    pk = campaign_new.pk
    response = client_user_campaign_change.post(
        f"/campaign/{pk}/workflow/",
        {
            "transition": "wf_activate",
            "comment": "",
        },
    )
    assert response.status_code == 302
    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert f"Successfully processed workflow step on “{campaign_new}”" in messages


@pytest.mark.django_db
def test_workflow_view_post_creates_workflow_info(client_user_campaign_change: Client, campaign_new):
    pk = campaign_new.pk
    client_user_campaign_change.post(
        f"/campaign/{pk}/workflow/",
        {
            "transition": "wf_activate",
            "comment": "",
        },
    )
    assert WorkflowInfo.objects.filter(
        workflow_object_pk=str(pk),
        transition="wf_activate",
        state_old=CampaignState.NEW,
        state_new=CampaignState.ACTIVE,
    ).exists()


@pytest.mark.django_db
def test_workflow_view_post_required_comment_missing(client_user_campaign_change: Client, campaign_new):
    """POST with required-comment transition but empty comment → form error, state unchanged."""
    pk = campaign_new.pk
    response = client_user_campaign_change.post(
        f"/campaign/{pk}/workflow/",
        {
            "transition": "wf_cancel_new",
            "comment": "",
        },
    )
    assert response.status_code == 200  # form invalid, re-render
    campaign_new.refresh_from_db()
    assert campaign_new.state == CampaignState.NEW  # state unchanged


@pytest.mark.django_db
def test_workflow_view_post_required_comment_provided(client_user_campaign_change: Client, campaign_new):
    pk = campaign_new.pk
    response = client_user_campaign_change.post(
        f"/campaign/{pk}/workflow/",
        {
            "transition": "wf_cancel_new",
            "comment": "Need to cancel this campaign",
        },
    )
    assert response.status_code == 302
    campaign_new.refresh_from_db()
    assert campaign_new.state == CampaignState.CANCELED
    info = WorkflowInfo.objects.get(workflow_object_pk=str(pk), transition="wf_cancel_new")
    assert info.comment == "Need to cancel this campaign"


@pytest.mark.django_db
def test_workflow_view_post_optional_comment_without(client_user_campaign_change: Client, campaign_active):
    pk = campaign_active.pk
    response = client_user_campaign_change.post(
        f"/campaign/{pk}/workflow/",
        {
            "transition": "wf_done",
            "comment": "",
        },
    )
    assert response.status_code == 302
    campaign_active.refresh_from_db()
    assert campaign_active.state == CampaignState.SUCCESS


@pytest.mark.django_db
def test_workflow_view_post_optional_comment_with(client_user_campaign_change: Client, campaign_active):
    pk = campaign_active.pk
    response = client_user_campaign_change.post(
        f"/campaign/{pk}/workflow/",
        {
            "transition": "wf_done",
            "comment": "Campaign completed successfully",
        },
    )
    assert response.status_code == 302
    campaign_active.refresh_from_db()
    assert campaign_active.state == CampaignState.SUCCESS
    info = WorkflowInfo.objects.get(workflow_object_pk=str(pk), transition="wf_done")
    assert info.comment == "Campaign completed successfully"


@pytest.mark.django_db
def test_workflow_view_post_unavailable_transition_form_error(client_user_campaign_change: Client, campaign_new):
    """Submitting a transition not available for the current state is rejected by form validation."""
    pk = campaign_new.pk
    response = client_user_campaign_change.post(
        f"/campaign/{pk}/workflow/",
        {
            "transition": "wf_done",  # only available from ACTIVE, not NEW
            "comment": "",
        },
    )
    # form validation rejects the choice; view re-renders the form
    assert response.status_code == 200
    campaign_new.refresh_from_db()
    assert campaign_new.state == CampaignState.NEW  # state unchanged


@pytest.mark.django_db
def test_workflow_history_after_multiple_transitions(client_user_campaign_change: Client, campaign_new):
    pk = campaign_new.pk

    # Transition 1: Activate
    client_user_campaign_change.post(
        f"/campaign/{pk}/workflow/",
        {
            "transition": "wf_activate",
            "comment": "",
        },
    )

    # Transition 2: Done (with comment)
    client_user_campaign_change.post(
        f"/campaign/{pk}/workflow/",
        {
            "transition": "wf_done",
            "comment": "All done",
        },
    )

    campaign_new.refresh_from_db()
    assert campaign_new.state == CampaignState.SUCCESS

    assert WorkflowInfo.objects.filter(workflow_object_pk=str(pk)).count() == 2

    history = campaign_new.workflow_data
    assert len(history) == 2
    assert history[0]["transition"] == "wf_activate"
    assert history[0]["state_old"] == CampaignState.NEW
    assert history[0]["state_new"] == CampaignState.ACTIVE
    assert history[1]["transition"] == "wf_done"
    assert history[1]["state_old"] == CampaignState.ACTIVE
    assert history[1]["state_new"] == CampaignState.SUCCESS
    assert history[1]["comment"] == "All done"


@pytest.mark.django_db
def test_workflow_history_transition_labels(client_user_campaign_change: Client, campaign_new):
    pk = campaign_new.pk
    client_user_campaign_change.post(
        f"/campaign/{pk}/workflow/",
        {
            "transition": "wf_activate",
            "comment": "",
        },
    )
    campaign_new.refresh_from_db()
    history = campaign_new.workflow_data
    assert history[0]["transition_label"] == "Activate"


@pytest.mark.django_db
def test_workflow_history_records_user(client_user_campaign_change: Client, campaign_new, user_campaign_change):
    pk = campaign_new.pk
    client_user_campaign_change.post(
        f"/campaign/{pk}/workflow/",
        {
            "transition": "wf_activate",
            "comment": "",
        },
    )
    info = WorkflowInfo.objects.get(workflow_object_pk=str(pk), transition="wf_activate")
    assert info.user == user_campaign_change


@pytest.mark.django_db
def test_workflow_info_null_comment_when_empty(client_user_campaign_change: Client, campaign_new):
    """A blank comment is stored as NULL in WorkflowInfo."""
    pk = campaign_new.pk
    client_user_campaign_change.post(
        f"/campaign/{pk}/workflow/",
        {
            "transition": "wf_activate",
            "comment": "",
        },
    )
    info = WorkflowInfo.objects.get(workflow_object_pk=str(pk), transition="wf_activate")
    assert info.comment is None


@pytest.mark.django_db
def test_workflow_view_get_contains_campaign_name(client_user_campaign_change: Client, campaign_new):
    response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/")
    assert response.status_code == 200
    assert campaign_new.name.encode() in response.content


# ---------------------------------------------------------------------------
# WorkflowViewPermissionRequired: access control tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_workflow_permission_required_allows_change_user(client_user_campaign_change: Client, campaign_new):
    """User with change permission can access the workflow view."""
    response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_workflow_permission_required_denies_view_only_user(client_user_campaign_view: Client, campaign_new):
    """User with only view permission is denied access (403)."""
    response = client_user_campaign_view.get(f"/campaign/{campaign_new.pk}/workflow/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_workflow_permission_required_denies_post_view_only_user(client_user_campaign_view: Client, campaign_new):
    """User with only view permission cannot POST a transition (403)."""
    response = client_user_campaign_view.post(
        f"/campaign/{campaign_new.pk}/workflow/",
        {
            "transition": "wf_activate",
            "comment": "",
        },
    )
    assert response.status_code == 403
    campaign_new.refresh_from_db()
    assert campaign_new.state == CampaignState.NEW  # state unchanged


@pytest.mark.django_db
def test_workflow_permission_required_redirects_anonymous(client: Client, campaign_new):
    """Anonymous user is redirected to the login page."""
    response = client.get(f"/campaign/{campaign_new.pk}/workflow/")
    assert response.status_code == 302
    assert "/login" in response["Location"]


# ---------------------------------------------------------------------------
# WorkflowView.checks() system checks
# ---------------------------------------------------------------------------


def _errors(view_cls):
    """Collect all error messages from a view's checks()."""
    return [msg for chk in view_cls.checks() for msg in chk.messages()]


def _error_ids(view_cls):
    return {e.id for e in _errors(view_cls)}


def test_workflow_view_checks_pass():
    """A correctly configured WorkflowView produces no check errors."""
    from tests.test1.app.views import CampaignWorkflowView

    assert _errors(CampaignWorkflowView) == []


def test_workflow_view_checks_missing_form_class():
    """Missing form_class yields E230."""
    from crud_views_workflow.lib.views import WorkflowView

    class NoFormView(WorkflowView):
        cv_key = "wf"
        cv_path = "wf"
        # form_class deliberately left as None (the WorkflowView default)

    assert "viewset.E230" in _error_ids(NoFormView)


def test_workflow_view_checks_transition_label_none():
    """cv_transition_label=None yields E231."""
    from crud_views_workflow.lib.forms import WorkflowForm
    from crud_views_workflow.lib.views import WorkflowView

    class NoLabelView(WorkflowView):
        cv_key = "wf"
        cv_path = "wf"
        form_class = WorkflowForm
        cv_transition_label = None

    assert "viewset.E231" in _error_ids(NoLabelView)


def test_workflow_view_checks_comment_label_none():
    """cv_comment_label=None yields E232."""
    from crud_views_workflow.lib.forms import WorkflowForm
    from crud_views_workflow.lib.views import WorkflowView

    class NoCommentLabelView(WorkflowView):
        cv_key = "wf"
        cv_path = "wf"
        form_class = WorkflowForm
        cv_comment_label = None

    assert "viewset.E232" in _error_ids(NoCommentLabelView)


def test_workflow_view_checks_model_not_mixin():
    """Model that does not extend WorkflowModelMixin yields E233."""
    from unittest.mock import MagicMock

    from crud_views_workflow.lib.forms import WorkflowForm
    from crud_views_workflow.lib.views import WorkflowView

    class PlainModel:
        pass

    class BadModelView(WorkflowView):
        cv_key = "wf"
        cv_path = "wf"
        form_class = WorkflowForm

    mock_viewset = MagicMock()
    mock_viewset.model = PlainModel
    BadModelView.cv_viewset = mock_viewset

    assert "viewset.E233" in _error_ids(BadModelView)


def test_workflow_view_checks_model_missing_state_choices():
    """WorkflowModelMixin model without STATE_CHOICES set yields E234."""
    from unittest.mock import MagicMock

    from crud_views_workflow.lib.forms import WorkflowForm
    from crud_views_workflow.lib.mixins import WorkflowModelMixin
    from crud_views_workflow.lib.views import WorkflowView

    class NoChoicesModel(WorkflowModelMixin):
        STATE_CHOICES = None
        STATE_BADGES = {"active": BadgeEnum.INFO}

    class NoChoicesView(WorkflowView):
        cv_key = "wf"
        cv_path = "wf"
        form_class = WorkflowForm

    mock_viewset = MagicMock()
    mock_viewset.model = NoChoicesModel
    NoChoicesView.cv_viewset = mock_viewset

    assert "viewset.E234" in _error_ids(NoChoicesView)


def test_workflow_view_checks_model_missing_state_badges():
    """WorkflowModelMixin model without STATE_BADGES set yields E235."""
    from unittest.mock import MagicMock

    from crud_views_workflow.lib.forms import WorkflowForm
    from crud_views_workflow.lib.mixins import WorkflowModelMixin
    from crud_views_workflow.lib.views import WorkflowView

    class NoBadgesModel(WorkflowModelMixin):
        STATE_CHOICES = object()
        STATE_BADGES = None

    class NoBadgesView(WorkflowView):
        cv_key = "wf"
        cv_path = "wf"
        form_class = WorkflowForm

    mock_viewset = MagicMock()
    mock_viewset.model = NoBadgesModel
    NoBadgesView.cv_viewset = mock_viewset

    assert "viewset.E235" in _error_ids(NoBadgesView)


# ---------------------------------------------------------------------------
# Hook placement (issue #31): transition logic must live in cv_form_valid,
# leaving cv_form_valid_hook free as the user extension point.
# ---------------------------------------------------------------------------


def test_transition_logic_lives_in_cv_form_valid():
    """
    WorkflowView must do its framework work in cv_form_valid (like Create/Update/FormSet views)
    and must NOT occupy cv_form_valid_hook, which is reserved for user subclasses.
    """
    from crud_views_workflow.lib.views import WorkflowView

    assert "cv_form_valid" in vars(WorkflowView)
    assert "cv_form_valid_hook" not in vars(WorkflowView)


@pytest.mark.django_db
def test_user_hook_override_keeps_transition(client_user_campaign_change: Client, campaign_new, monkeypatch):
    """
    A user subclass overriding cv_form_valid_hook (without calling super()) must not destroy
    transition execution — regression guard for issue #31.
    """
    from tests.test1.app.views import CampaignWorkflowView

    calls = []
    monkeypatch.setattr(CampaignWorkflowView, "cv_form_valid_hook", lambda self, context: calls.append("hook"))

    response = client_user_campaign_change.post(
        f"/campaign/{campaign_new.pk}/workflow/",
        {"transition": "wf_activate", "comment": ""},
    )
    assert response.status_code == 302
    campaign_new.refresh_from_db()
    assert campaign_new.state == CampaignState.ACTIVE
    assert calls == ["hook"]
