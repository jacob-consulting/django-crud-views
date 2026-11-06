"""Contracts shared by workflow forms, requests and standalone execution."""

import inspect
from contextlib import contextmanager
from functools import wraps

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation, ValidationError
from django.db import connections, router, transaction
from django.db.models.query import QuerySet
from django.forms import CharField
from django.test import Client, RequestFactory

from crud_views_workflow.lib.enums import WorkflowComment
from crud_views_workflow.lib.forms import WorkflowForm
from crud_views_workflow.models import WorkflowInfo
from tests.test1.app.models import Campaign, CampaignState, Publisher
from tests.test1.app.views import CampaignWorkflowForm, CampaignWorkflowView


@pytest.fixture
def workflow_worlds(request):
    """Independent rows deliberately collide by PK, never by identity."""
    from tests.test1.app.views import cv_campaign

    # ViewSet permission names are process-cached metadata. Resolve them from
    # the untouched default migration rows before creating divergent shard IDs.
    previous_permissions = cv_campaign._default_permissions
    request.addfinalizer(lambda: setattr(cv_campaign, "_default_permissions", previous_permissions))
    cv_campaign._default_permissions = None
    assert cv_campaign.permissions["change"] == "app.change_campaign"
    ContentType.objects.clear_cache()
    worlds = {}
    for using in ("default", "shard"):
        obj = Campaign.objects.using(using).create(pk=41, name=f"{using} campaign")
        actor = User.objects.db_manager(using).create_user(
            pk=51, username=f"{using} actor", is_superuser=True, is_staff=True
        )
        if using == "shard":
            ContentType.objects.using(using).filter(app_label="app", model="campaign").delete()
            ContentType.objects.using(using).create(pk=10001, app_label="app", model="campaign")
        worlds[using] = (obj, actor, ContentType.objects.db_manager(using).get_for_model(Campaign))
    assert worlds["default"][2].pk != worlds["shard"][2].pk
    yield worlds
    ContentType.objects.clear_cache()


pytestmark = pytest.mark.django_db


class TestWorkflowTracer:
    def test_radio_business_refusal_then_success(self, client_user_campaign_change, campaign_new, monkeypatch):
        calls = []
        blocked = True

        def check(obj, name, *, user):
            calls.append((obj.pk, name, user.pk))
            if blocked:
                raise ValidationError(
                    [
                        ValidationError("Missing %(item)s", params={"item": "budget"}),
                        "Missing approval",
                    ]
                )

        monkeypatch.setattr(Campaign, "workflow_check_transition", check, raising=False)
        url = f"/campaign/{campaign_new.pk}/workflow/"
        response = client_user_campaign_change.get(url)
        assert response.status_code == 200
        assert calls == []
        assert response.context["form"].fields["transition"].widget.__class__.__name__ == "RadioSelect"

        response = client_user_campaign_change.post(url, {"transition": "wf_cancel_new", "comment": "  "})
        assert response.status_code == 200
        form = response.context["form"]
        assert list(form.errors["transition"]) == ["Missing budget", "Missing approval"]
        assert list(form.errors["comment"]) == ["Comment is required for this transition"]
        assert not form.non_field_errors()
        assert form.data["comment"] == "  "
        campaign_new.refresh_from_db()
        assert campaign_new.state == CampaignState.NEW
        assert not WorkflowInfo.objects.exists()

        blocked = False
        response = client_user_campaign_change.post(url, {"transition": "wf_cancel_new", "comment": "  reason  "})
        assert response.status_code == 302
        campaign_new.refresh_from_db()
        assert campaign_new.state == CampaignState.CANCELED
        info = WorkflowInfo.objects.get()
        assert info.transition == "wf_cancel_new"
        assert info.state_old == CampaignState.NEW
        assert info.state_new == CampaignState.CANCELED
        assert info.comment == "reason"
        assert info.user_id == response.wsgi_request.user.pk
        assert info.data is None
        assert info.workflow_object_pk == str(campaign_new.pk)
        assert info.workflow_object_content_type == ContentType.objects.get_for_model(Campaign)

    def test_inheritable_clean(self, client_user_campaign_change, campaign_new, monkeypatch):
        class InheritedForm(CampaignWorkflowForm):
            def clean(self):
                cleaned = super().clean()
                assert isinstance(cleaned, dict)
                cleaned["subclass_value"] = "retained"
                return cleaned

        monkeypatch.setattr(CampaignWorkflowView, "form_class", InheritedForm)
        response = client_user_campaign_change.post(
            f"/campaign/{campaign_new.pk}/workflow/", {"transition": "wf_activate", "comment": ""}
        )
        assert response.status_code == 302

    @pytest.mark.parametrize(
        "name, comment, valid, field",
        [
            ("wf_cancel_new", "reason", True, None),
            ("wf_cancel_new", "  ", False, "comment"),
            ("forged", "reason", False, "transition"),
            ("", "reason", False, "transition"),
        ],
    )
    def test_ownerless_form(self, name, comment, valid, field):
        form = WorkflowForm(
            data={"transition": name, "comment": comment},
            cv_view=None,
            choices=[("wf_cancel_new", "Cancel")],
            transition_comments={"wf_cancel_new": WorkflowComment.REQUIRED},
        )
        assert form.is_valid() is valid
        if field:
            assert field in form.errors
        else:
            assert form.clean() == {"transition": name, "comment": comment}


class TestWorkflowHelper:
    def test_exact_public_signature(self, campaign_new, user_campaign_change):
        import crud_views_workflow.lib as workflow

        helper = getattr(workflow, "run_transition", None)
        assert callable(helper), "run_transition must be exported from crud_views_workflow.lib"
        assert "run_transition" in workflow.__all__
        assert str(inspect.signature(helper)) == "(object, name, *, user, comment=None)"
        with pytest.raises(TypeError):
            helper(campaign_new, "wf_activate")
        with pytest.raises(TypeError):
            helper(campaign_new, "wf_activate", user_campaign_change)

    def test_complete_history_and_view_parity(
        self, campaign_new, user_campaign_change, client_user_campaign_change, monkeypatch
    ):
        from crud_views_workflow.lib import run_transition

        original = Campaign.wf_activate

        @wraps(original)
        def transition(obj, *, by, comment):
            original(obj, by=by, comment=comment)
            return {"actor": by.pk, "comment": comment}

        monkeypatch.setattr(Campaign, "wf_activate", transition)
        info = run_transition(campaign_new, "wf_activate", user=user_campaign_change, comment="  note  ")
        assert isinstance(info, WorkflowInfo)
        assert info.pk is not None
        assert info.user == user_campaign_change
        assert info.state_old == CampaignState.NEW
        assert info.state_new == CampaignState.ACTIVE
        assert info.comment == "note"
        assert info.data == {"actor": user_campaign_change.pk, "comment": "note"}
        assert info.workflow_object_pk == str(campaign_new.pk)
        assert info.workflow_object_content_type == ContentType.objects.get_for_model(Campaign)
        assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.ACTIVE
        other = Campaign.objects.create(name="View parity")
        response = client_user_campaign_change.post(
            f"/campaign/{other.pk}/workflow/", {"transition": "wf_activate", "comment": "  note  "}
        )
        assert response.status_code == 302
        view_info = WorkflowInfo.objects.get(workflow_object_pk=str(other.pk))
        for attr in (
            "transition",
            "user_id",
            "state_old",
            "state_new",
            "comment",
            "data",
            "workflow_object_content_type_id",
        ):
            assert getattr(info, attr) == getattr(view_info, attr)

    @pytest.mark.parametrize("name", [None, "", "unknown", "save", "__class__", "wf_done"])
    def test_unavailable_names_never_expose_blockers(self, campaign_new, user_campaign_change, monkeypatch, name):
        from crud_views_workflow.lib import run_transition

        def forbidden_check(*args, **kwargs):
            pytest.fail("Unavailable transition disclosed business validation")

        monkeypatch.setattr(Campaign, "workflow_check_transition", forbidden_check)
        with pytest.raises(SuspiciousOperation):
            run_transition(campaign_new, name, user=user_campaign_change)
        assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.NEW
        assert not WorkflowInfo.objects.exists()

    @pytest.mark.parametrize("gate", ["permission", "condition"])
    def test_fsm_gates_precede_business(self, campaign_new, user_campaign_change, monkeypatch, gate):
        from crud_views_workflow.lib import run_transition

        step = next(step for step in campaign_new.get_all_state_transitions() if step.name == "wf_activate")
        if gate == "permission":
            monkeypatch.setattr(step, "permission", lambda obj, user: False)
        else:
            monkeypatch.setattr(step, "conditions", [lambda obj: False])

        def forbidden_check(*args, **kwargs):
            pytest.fail("Unavailable transition disclosed business validation")

        monkeypatch.setattr(Campaign, "workflow_check_transition", forbidden_check)
        with pytest.raises(SuspiciousOperation):
            run_transition(campaign_new, "wf_activate", user=user_campaign_change)
        assert not WorkflowInfo.objects.exists()

    def test_anonymous_actor_precondition(self, campaign_new, monkeypatch):
        from crud_views_workflow.lib import run_transition

        def forbidden(*args, **kwargs):
            pytest.fail("Unsupported actor reached business or dispatch")

        monkeypatch.setattr(Campaign, "workflow_check_transition", forbidden)
        monkeypatch.setattr(Campaign, "wf_activate", forbidden)
        with pytest.raises(ImproperlyConfigured, match=r"authenticated.*saved|saved.*authenticated"):
            run_transition(campaign_new, "wf_activate", user=AnonymousUser())
        assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.NEW
        assert not WorkflowInfo.objects.exists()

    @pytest.mark.parametrize("comment", [None, "", " \t ", "  reason  "])
    @pytest.mark.parametrize("policy", list(WorkflowComment))
    @pytest.mark.parametrize("use_default", [False, True])
    def test_comment_policies(self, campaign_new, user_campaign_change, monkeypatch, policy, comment, use_default):
        from crud_views_workflow.lib import run_transition

        step = next(step for step in campaign_new.get_all_state_transitions() if step.name == "wf_activate")
        if use_default:
            monkeypatch.delitem(step.custom, "comment")
            monkeypatch.setattr(Campaign, "COMMENT_DEFAULT", policy)
        else:
            monkeypatch.setitem(step.custom, "comment", policy)
        expected = comment.strip() or None if isinstance(comment, str) else None
        if policy == WorkflowComment.REQUIRED and expected is None:
            with pytest.raises(ValidationError, match="Comment is required"):
                run_transition(campaign_new, "wf_activate", user=user_campaign_change, comment=comment)
            assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.NEW
            assert not WorkflowInfo.objects.exists()
        else:
            info = run_transition(campaign_new, "wf_activate", user=user_campaign_change, comment=comment)
            assert info.comment == expected

    @pytest.mark.parametrize("messages", ["One blocker", ["First blocker", "Second blocker"]])
    def test_business_error_order(self, campaign_new, user_campaign_change, monkeypatch, messages):
        from crud_views_workflow.lib import run_transition

        def check(obj, name, *, user):
            raise ValidationError(messages)

        monkeypatch.setattr(Campaign, "workflow_check_transition", check)
        with pytest.raises(ValidationError) as caught:
            run_transition(campaign_new, "wf_activate", user=user_campaign_change)
        assert caught.value.messages == ([messages] if isinstance(messages, str) else messages)
        assert not WorkflowInfo.objects.exists()

    def test_dictionary_errors_propagate_clearly(self, campaign_new, user_campaign_change, monkeypatch):
        from crud_views_workflow.lib import run_transition

        def check(obj, name, *, user):
            raise ValidationError({"name": "Unsupported field error"})

        monkeypatch.setattr(Campaign, "workflow_check_transition", check)
        with pytest.raises(TypeError, match="single/list ValidationError, not a dictionary"):
            run_transition(campaign_new, "wf_activate", user=user_campaign_change)
        assert not WorkflowInfo.objects.exists()


@pytest.mark.django_db(transaction=True)
class TestWorkflowRefusal:
    @pytest.mark.parametrize("atomic", [False, True])
    @pytest.mark.parametrize("modal", [False, True])
    @pytest.mark.parametrize("refusal_kind", ["business", "comment"])
    def test_late_refusal(self, client_user_campaign_change, campaign_new, monkeypatch, atomic, modal, refusal_kind):
        class CustomForm(CampaignWorkflowForm):
            extra = CharField()

        seen = {"execution": False, "selected": [], "reload": [], "invalid": [], "depth": 0}
        real_process = CampaignWorkflowView.cv_form_valid
        real_get_object = CampaignWorkflowView.get_object
        real_atomic = transaction.atomic
        field = Campaign._meta.get_field("state")
        monkeypatch.setattr(field, "protected", True)
        monkeypatch.setattr(CampaignWorkflowView, "cv_atomic", atomic)
        monkeypatch.setattr(CampaignWorkflowView, "cv_modal", modal)
        monkeypatch.setattr(CampaignWorkflowView, "form_class", CustomForm)

        def alias(view):
            assert view.object.pk == campaign_new.pk
            seen["selected"].append(view.object._state.db)
            return "default"

        @contextmanager
        def boundary(*args, **kwargs):
            assert kwargs["using"] == "default"
            seen["depth"] += 1
            try:
                with real_atomic(*args, **kwargs):
                    yield
            finally:
                seen["depth"] -= 1

        def get_object(view, queryset=None):
            if queryset is not None:
                seen["reload"].append(queryset.db)
                assert seen["depth"] == 0
                assert not connections["default"].in_atomic_block
            return real_get_object(view, queryset=queryset)

        def process(view, context):
            seen["execution"] = True  # explicit boundary; no nth-hook-call assumption
            seen["form"] = context["form"]
            context["workflow_info"] = "stale record"
            context["stale_history"] = "discard me"
            if refusal_kind == "comment":
                step = next(t for t in view.object.get_all_state_transitions() if t.name == "wf_activate")
                monkeypatch.setitem(step.custom, "comment", WorkflowComment.REQUIRED)
            return real_process(view, context)

        def check(obj, name, *, user):
            if seen["execution"] and refusal_kind == "business":
                # Deliberately simulate dirty Python state and a database write inside
                # the engine to prove rollback/fresh-fetch recovery. Real hooks are read-only.
                obj.__dict__["state"] = CampaignState.ACTIVE
                Campaign.objects.filter(pk=obj.pk).update(name="must roll back")
                raise ValidationError(["Late first blocker", "Late second blocker"])

        def unexpected(*args, **kwargs):
            pytest.fail("Expected refusal entered a success hook/callback")

        monkeypatch.setattr(CampaignWorkflowView, "cv_get_db_alias", alias)
        monkeypatch.setattr(CampaignWorkflowView, "get_object", get_object)
        monkeypatch.setattr(CampaignWorkflowView, "cv_form_valid", process)
        monkeypatch.setattr(CampaignWorkflowView, "cv_form_valid_hook", unexpected)
        monkeypatch.setattr(CampaignWorkflowView, "on_transition", unexpected)
        monkeypatch.setattr(CampaignWorkflowView, "cv_on_commit", unexpected)
        monkeypatch.setattr(
            CampaignWorkflowView, "cv_form_invalid_hook", lambda view, context: seen["invalid"].append(context)
        )
        monkeypatch.setattr(Campaign, "workflow_check_transition", check)
        monkeypatch.setattr(transaction, "atomic", boundary)
        client_user_campaign_change.raise_request_exception = False
        raw_comment = "  retained input  " if refusal_kind == "business" else " \t "
        response = client_user_campaign_change.post(
            f"/campaign/{campaign_new.pk}/workflow/",
            {"transition": "wf_activate", "comment": raw_comment, "extra": "  custom input  "},
            headers={"X-CV-Modal": "true"} if modal else {},
        )
        assert response.status_code == (422 if modal else 200)
        context = seen["invalid"][0]
        form = context["form"]
        assert form is seen["form"]
        assert form.data["comment"] == raw_comment
        assert form.data["extra"] == "  custom input  "
        assert not form.non_field_errors()
        expected_field = "transition" if refusal_kind == "business" else "comment"
        expected_errors = (
            ["Late first blocker", "Late second blocker"]
            if refusal_kind == "business"
            else ["Comment is required for this transition"]
        )
        assert list(form.errors[expected_field]) == expected_errors
        assert "workflow_info" not in context
        assert "stale_history" not in context
        assert context["object"].state == CampaignState.NEW
        assert context["object"].name == campaign_new.name
        assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.NEW
        assert Campaign.objects.get(pk=campaign_new.pk).name == campaign_new.name
        assert not WorkflowInfo.objects.exists()
        assert not list(get_messages(response.wsgi_request))
        assert seen["selected"] == ["default"]
        assert seen["reload"] == ["default"]
        assert len(seen["invalid"]) == 1

    @pytest.mark.parametrize("atomic", [False, True])
    def test_selected_alias_for_success_callback(self, client_user_campaign_change, campaign_new, monkeypatch, atomic):
        selected, registered, called = [], [], []
        original_on_commit = transaction.on_commit
        original_atomic = CampaignWorkflowView.cv_get_atomic
        boundaries = []

        def select(view):
            selected.append(view.object.pk)
            return "default"

        def register(func, using=None, robust=False):
            registered.append(using)
            return original_on_commit(func, using=using, robust=robust)

        def custom_atomic(view):
            boundaries.append(view._cv_get_workflow_db_alias())
            return original_atomic(view)

        monkeypatch.setattr(CampaignWorkflowView, "cv_atomic", atomic)
        monkeypatch.setattr(CampaignWorkflowView, "cv_get_db_alias", select)
        monkeypatch.setattr(CampaignWorkflowView, "cv_get_atomic", custom_atomic)
        monkeypatch.setattr(CampaignWorkflowView, "cv_on_commit", lambda view, context: called.append(context))
        monkeypatch.setattr(transaction, "on_commit", register)
        response = client_user_campaign_change.post(
            f"/campaign/{campaign_new.pk}/workflow/", {"transition": "wf_activate", "comment": ""}
        )
        assert response.status_code == 302
        assert selected == [campaign_new.pk]
        assert boundaries == registered == ["default"]
        assert len(called) == 1
        assert called[0]["workflow_info"].pk == WorkflowInfo.objects.get().pk

    def test_refusal_reload_retains_queryset_scope(self, client_user_campaign_change, campaign_new, monkeypatch):
        executing = False
        original_process = CampaignWorkflowView.cv_form_valid
        original_queryset = CampaignWorkflowView.get_queryset

        def process(view, context):
            nonlocal executing
            executing = True
            return original_process(view, context)

        def check(obj, name, *, user):
            if executing:
                raise ValidationError("Late blocker")

        def scoped(view):
            queryset = original_queryset(view)
            return queryset.none() if executing else queryset

        monkeypatch.setattr(CampaignWorkflowView, "cv_form_valid", process)
        monkeypatch.setattr(CampaignWorkflowView, "get_queryset", scoped)
        monkeypatch.setattr(Campaign, "workflow_check_transition", check)
        response = client_user_campaign_change.post(
            f"/campaign/{campaign_new.pk}/workflow/", {"transition": "wf_activate", "comment": ""}
        )
        assert response.status_code == 404
        assert not WorkflowInfo.objects.exists()

    @pytest.mark.parametrize("atomic", [False, True])
    def test_ordinary_execution_validation_error_propagates(
        self, client_user_campaign_change, campaign_new, monkeypatch, atomic
    ):
        error = ValidationError("Callback defect")

        def on_transition(*args, **kwargs):
            raise error

        monkeypatch.setattr(CampaignWorkflowView, "cv_atomic", atomic)
        monkeypatch.setattr(CampaignWorkflowView, "on_transition", on_transition)
        with pytest.raises(ValidationError) as caught:
            client_user_campaign_change.post(
                f"/campaign/{campaign_new.pk}/workflow/", {"transition": "wf_activate", "comment": ""}
            )
        assert caught.value is error
        assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.NEW
        assert not WorkflowInfo.objects.exists()


@pytest.mark.django_db(transaction=True, databases=["default", "shard"])
class TestWorkflowDatabase:
    def test_instance_fallback_history_readback(self, workflow_worlds, monkeypatch):
        from crud_views_workflow.lib import run_transition

        monkeypatch.setattr(router, "routers", [])
        obj, actor, content_type = workflow_worlds["shard"]
        info = run_transition(obj, "wf_activate", user=actor, comment="  shard note  ")
        queryset = obj.get_workflow_info_queryset()
        assert queryset.db == "shard", "History reads must stay on the persisted object's database"
        assert list(queryset) == [info]
        assert info.user.username == "shard actor"
        assert info.workflow_object_content_type_id == content_type.pk
        assert info.workflow_object.name == "shard campaign"
        assert obj.workflow_data[0]["comment"] == "shard note"
        assert not WorkflowInfo.objects.using("default").exists()
        assert Campaign.objects.using("default").get(pk=obj.pk).state == CampaignState.NEW

    @pytest.mark.parametrize("history_route", [None, "default"])
    @pytest.mark.parametrize("path", ["helper", "request"])
    def test_selected_shard_identity(self, workflow_worlds, database_routes, monkeypatch, history_route, path):
        from crud_views_workflow.lib import run_transition

        obj, actor, content_type = workflow_worlds["shard"]
        selected, callbacks = [], []

        def select(view):
            selected.append((view.object._state.db, view.request.user._state.db))
            return "shard"

        def committed(view, context):
            assert not connections["shard"].in_atomic_block
            callbacks.append(context["workflow_info"])

        monkeypatch.setattr(CampaignWorkflowView, "cv_get_db_alias", select)
        monkeypatch.setattr(CampaignWorkflowView, "cv_on_commit", committed)
        original = Campaign.wf_activate

        @wraps(original)
        def activate(obj, *, by, comment):
            original(obj, by=by, comment=comment)
            return {"actor": by.username, "alias": obj._state.db}

        monkeypatch.setattr(Campaign, "wf_activate", activate)
        # Holding default open proves successful callbacks use shard.
        with (
            database_routes("shard", {WorkflowInfo: history_route, ContentType: history_route}),
            transaction.atomic(using="default"),
        ):
            if path == "helper":
                info = run_transition(obj, "wf_activate", user=actor, comment="  routed  ")
            else:
                client = Client()
                client.force_login(actor)
                response = client.post(
                    f"/campaign/{obj.pk}/workflow/", {"transition": "wf_activate", "comment": "  routed  "}
                )
                assert response.status_code == 302
                assert selected == [("shard", "shard")]
                assert len(callbacks) == 1
                info = callbacks[0]
            assert info._state.db == "shard"
            assert info.user.username == actor.username
            assert info.user._state.db == "shard"
            assert info.workflow_object_content_type_id == content_type.pk
            assert info.workflow_object._state.db == "shard"
            assert info.workflow_object.name == obj.name
            assert info.state_old == CampaignState.NEW
            assert info.state_new == CampaignState.ACTIVE
            assert info.data == {"actor": actor.username, "alias": "shard"}
            assert info.comment == "routed"
            assert list(obj.get_workflow_info_queryset()) == [info]
            assert obj.workflow_data[0]["user"].username == "shard actor"
        assert Campaign.objects.using("shard").get(pk=obj.pk).state == CampaignState.ACTIVE
        assert Campaign.objects.using("default").get(pk=obj.pk).state == CampaignState.NEW
        assert not WorkflowInfo.objects.using("default").exists()

    @pytest.mark.parametrize("invalid", ["unsaved-object", "unsaved-user", "other-object", "other-user"])
    def test_invalid_identity_precedes_business_and_dispatch(
        self, workflow_worlds, database_routes, monkeypatch, invalid
    ):
        from crud_views_workflow.lib import run_transition

        obj, actor, _ = workflow_worlds["shard"]
        if invalid == "unsaved-object":
            obj = Campaign(pk=41, name="Not saved")
        elif invalid == "unsaved-user":
            actor = User(pk=51, username="Not saved")
        elif invalid == "other-object":
            obj = workflow_worlds["default"][0]
        else:
            actor = workflow_worlds["default"][1]

        def forbidden(*args, **kwargs):
            pytest.fail("Invalid identity reached execution business validation or transition")

        monkeypatch.setattr(Campaign, "workflow_check_transition", forbidden)
        monkeypatch.setattr(Campaign, "wf_activate", forbidden)
        with database_routes("shard"), pytest.raises(ImproperlyConfigured, match="must be saved"):
            run_transition(obj, "wf_activate", user=actor)
        for using in ("default", "shard"):
            assert Campaign.objects.using(using).get(pk=41).state == CampaignState.NEW
            assert not WorkflowInfo.objects.using(using).exists()

    def test_unaligned_view_override_rejected(self, workflow_worlds, database_routes, monkeypatch):
        obj, actor, _ = workflow_worlds["default"]
        selected, callbacks = [], []

        def select(view):
            selected.append((view.object._state.db, view.request.user._state.db))
            return "shard"

        def forbidden(*args, **kwargs):
            pytest.fail("Mismatched view override dispatched transition")

        monkeypatch.setattr(CampaignWorkflowView, "cv_get_db_alias", select)
        monkeypatch.setattr(CampaignWorkflowView, "cv_on_commit", lambda view, context: callbacks.append(context))
        monkeypatch.setattr(Campaign, "wf_activate", forbidden)
        with database_routes("default"):
            client = Client()
            client.force_login(actor)
            with pytest.raises(ImproperlyConfigured, match="must be saved"):
                client.post(f"/campaign/{obj.pk}/workflow/", {"transition": "wf_activate", "comment": ""})
        assert selected == [("default", "default")]
        assert callbacks == []
        for using in ("default", "shard"):
            assert Campaign.objects.using(using).get(pk=41).state == CampaignState.NEW
            assert not WorkflowInfo.objects.using(using).exists()

    def test_anonymous_base_view_rejected(self, campaign_new, monkeypatch):
        from crud_views.lib.crispy import CrispyViewMixin
        from crud_views_workflow.lib.views import WorkflowView
        from tests.test1.app.views import cv_campaign

        class BaseWorkflow(CrispyViewMixin, WorkflowView):
            form_class = CampaignWorkflowForm

        BaseWorkflow.cv_viewset = cv_campaign  # no test-time registry replacement
        calls = []
        monkeypatch.setattr(BaseWorkflow, "cv_on_commit", lambda view, context: calls.append(context))

        def forbidden(*args, **kwargs):
            pytest.fail("Anonymous actor dispatched a transition")

        monkeypatch.setattr(Campaign, "wf_activate", forbidden)
        request = RequestFactory().post(
            f"/campaign/{campaign_new.pk}/workflow/", {"transition": "wf_activate", "comment": ""}
        )
        request.user = AnonymousUser()
        with pytest.raises(ImproperlyConfigured, match="authenticated and saved"):
            BaseWorkflow.as_view()(request, pk=campaign_new.pk)
        assert calls == []
        assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.NEW
        assert not WorkflowInfo.objects.exists()

    def test_split_read_write_inputs_rejected(self, workflow_worlds, monkeypatch):
        from crud_views_workflow.lib import run_transition

        class SplitRouter:
            def db_for_read(self, model, **hints):
                return "shard" if model in (Campaign, User) else "default"

            def db_for_write(self, model, **hints):
                return "default"

        monkeypatch.setattr(router, "routers", [SplitRouter()])
        obj, actor, _ = workflow_worlds["shard"]
        default_actor = workflow_worlds["default"][1]
        # Authenticate the shard-loaded identity using the default session store.
        User.objects.using("shard").filter(pk=actor.pk).update(password=default_actor.password)
        actor = User.objects.get(pk=actor.pk)
        checks, selected, callbacks = [], [], []

        def check(obj, name, *, user):
            checks.append((obj._state.db, user._state.db))

        def forbidden(*args, **kwargs):
            pytest.fail("Read-shard/write-default mismatch dispatched a transition")

        original_select = CampaignWorkflowView.cv_get_db_alias

        def select(view):
            using = original_select(view)
            selected.append((view.object._state.db, view.request.user._state.db, using))
            return using

        monkeypatch.setattr(Campaign, "workflow_check_transition", check)
        monkeypatch.setattr(Campaign, "wf_activate", forbidden)
        monkeypatch.setattr(CampaignWorkflowView, "cv_get_db_alias", select)
        monkeypatch.setattr(CampaignWorkflowView, "cv_on_commit", lambda view, context: callbacks.append(context))
        assert obj._state.db == actor._state.db == "shard"
        assert router.db_for_write(Campaign, instance=obj) == "default"
        with pytest.raises(ImproperlyConfigured, match="must be saved"):
            run_transition(obj, "wf_activate", user=actor)
        assert checks == []
        client = Client()
        client.force_login(default_actor)
        before = {using: list(Campaign.objects.using(using).values()) for using in ("default", "shard")}
        with pytest.raises(ImproperlyConfigured, match="must be saved"):
            client.post(f"/campaign/{obj.pk}/workflow/", {"transition": "wf_activate", "comment": ""})
        assert checks == [("shard", "shard")]  # existing side-effect-free form check only
        assert selected == [("shard", "shard", "default")]
        assert callbacks == []
        for using in ("default", "shard"):
            assert list(Campaign.objects.using(using).values()) == before[using]
            assert not WorkflowInfo.objects.using(using).exists()

    def test_unsaved_history_readback_uses_router_fallback(self, workflow_worlds, database_routes):
        unsaved = Campaign(name="Not executed")
        with database_routes("shard"):
            queryset = unsaved.get_workflow_info_queryset()
            assert queryset.db == "shard"
            assert list(queryset) == []


@pytest.mark.django_db(transaction=True, databases=["default", "shard"])
class TestWorkflowRollback:
    @pytest.mark.parametrize("using", ["default", "shard"])
    @pytest.mark.parametrize("error_type", [ValidationError, RuntimeError])
    @pytest.mark.parametrize(
        "path,atomic,stage",
        [
            (path, atomic, stage)
            for path, atomic in [("helper", False), ("request", False), ("request", True)]
            for stage in ["transition", "save", "content-type", "history", "on_transition"]
            if path == "request" or stage != "on_transition"
        ],
    )
    def test_failure_stages(
        self, workflow_worlds, database_routes, monkeypatch, using, error_type, path, atomic, stage
    ):
        from crud_views_workflow.lib import run_transition

        obj, actor, _ = workflow_worlds[using]
        error = error_type(f"Failure at {stage}")
        observed, callbacks = [], []
        executing = False
        original_transition = Campaign.wf_activate
        original_save = Campaign.save
        original_get_type = type(ContentType.objects).get_for_model
        original_create = QuerySet.create
        original_process = CampaignWorkflowView.cv_form_valid

        def fail():
            observed.append((stage, connections[using].in_atomic_block))
            # A real consumer follow-up write must participate in the same rollback.
            Publisher.objects.using(using).create(name="Follow-up must roll back")
            raise error

        @wraps(original_transition)
        def transition(obj, *, by, comment):
            result = original_transition(obj, by=by, comment=comment)
            assert obj.state == CampaignState.ACTIVE
            if stage == "transition":
                fail()
            return result

        def save(obj, *args, **kwargs):
            result = original_save(obj, *args, **kwargs)
            assert kwargs["using"] == using
            if stage == "save":
                fail()
            return result

        def get_type(manager, *args, **kwargs):
            result = original_get_type(manager, *args, **kwargs)
            if executing and stage == "content-type":
                assert manager.db == using
                fail()
            return result

        def create(queryset, **kwargs):
            result = original_create(queryset, **kwargs)
            if queryset.model is WorkflowInfo and stage == "history":
                assert result._state.db == using
                fail()
            return result

        def on_transition(view, *args):
            if stage == "on_transition":
                fail()

        def process(view, context):
            nonlocal executing
            executing = True
            return original_process(view, context)

        monkeypatch.setattr(Campaign, "wf_activate", transition)
        monkeypatch.setattr(Campaign, "save", save)
        monkeypatch.setattr(type(ContentType.objects), "get_for_model", get_type)
        monkeypatch.setattr(QuerySet, "create", create)
        monkeypatch.setattr(CampaignWorkflowView, "cv_atomic", atomic)
        monkeypatch.setattr(CampaignWorkflowView, "cv_form_valid", process)
        monkeypatch.setattr(CampaignWorkflowView, "on_transition", on_transition)
        monkeypatch.setattr(CampaignWorkflowView, "cv_on_commit", lambda view, context: callbacks.append(context))
        with database_routes(using), pytest.raises(error_type) as caught:
            if path == "helper":
                executing = True
                run_transition(obj, "wf_activate", user=actor, comment="reason")
            else:
                client = Client()
                client.force_login(actor)
                client.post(f"/campaign/{obj.pk}/workflow/", {"transition": "wf_activate", "comment": "reason"})
        assert caught.value is error  # ordinary ValidationError must never become a refusal
        assert observed == [(stage, True)]
        assert callbacks == []
        if path == "helper":
            assert obj.state == CampaignState.ACTIVE  # rollback does not repair Python instances
        for alias in ("default", "shard"):
            persisted = Campaign.objects.using(alias).get(pk=41)
            assert persisted.state == CampaignState.NEW
            assert persisted.name == f"{alias} campaign"
            assert not WorkflowInfo.objects.using(alias).exists()
            assert not Publisher.objects.using(alias).exists()

    @pytest.mark.parametrize("using", ["default", "shard"])
    @pytest.mark.parametrize("atomic", [False, True])
    def test_success_callback_and_followup_atomicity(
        self, workflow_worlds, database_routes, monkeypatch, using, atomic
    ):
        obj, actor, _ = workflow_worlds[using]
        other = "shard" if using == "default" else "default"
        observed, callbacks = [], []

        def on_transition(view, info, *args):
            assert info._state.db == using
            observed.append(connections[using].in_atomic_block)
            Publisher.objects.using(using).create(name="Committed follow-up")

        def on_commit(view, context):
            assert not connections[using].in_atomic_block
            info = context["workflow_info"]
            assert WorkflowInfo.objects.using(using).get(pk=info.pk).state_new == CampaignState.ACTIVE
            callbacks.append(info)

        monkeypatch.setattr(CampaignWorkflowView, "cv_atomic", atomic)
        monkeypatch.setattr(CampaignWorkflowView, "on_transition", on_transition)
        monkeypatch.setattr(CampaignWorkflowView, "cv_on_commit", on_commit)
        with database_routes(using), transaction.atomic(using=other):
            client = Client()
            client.force_login(actor)
            response = client.post(f"/campaign/{obj.pk}/workflow/", {"transition": "wf_activate", "comment": ""})
            assert response.status_code == 302
            assert observed == [True]
            assert len(callbacks) == 1
        assert callbacks[0]._state.db == using
        assert Publisher.objects.using(using).get().name == "Committed follow-up"
        assert not Publisher.objects.using(other).exists()
        assert not WorkflowInfo.objects.using(other).exists()

    @pytest.mark.parametrize("using", ["default", "shard"])
    def test_direct_decorated_call_remains_outside_helper(self, workflow_worlds, monkeypatch, using):
        obj, actor, _ = workflow_worlds[using]

        def check(*args, **kwargs):
            pytest.fail("Direct decorated calls must not invoke the new helper hook")

        monkeypatch.setattr(Campaign, "workflow_check_transition", check)
        obj.wf_activate(by=actor, comment="Direct call")
        assert obj.state == CampaignState.ACTIVE
        assert Campaign.objects.using(using).get(pk=obj.pk).state == CampaignState.NEW
        assert not WorkflowInfo.objects.using(using).exists()
