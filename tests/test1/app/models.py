import uuid

from django.db import models
from django_fsm import FSMField, transition
from ordered_model.models import OrderedModel
from polymorphic.models import PolymorphicModel

from crud_views_workflow.mixins import WorkflowMixin


class Author(OrderedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    pseudonym = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Publisher(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="books")

    def __str__(self):
        return self.title


class Campaign(WorkflowMixin, models.Model):
    class STATE:
        NEW = "new"
        ACTIVE = "active"
        SUCCESS = "success"
        CANCELED = "canceled"
        ERROR = "error"

    STATE_CHOICES = (
        (STATE.NEW, "New"),
        (STATE.ACTIVE, "Active"),
        (STATE.SUCCESS, "Success"),
        (STATE.CANCELED, "Cancelled"),
        (STATE.ERROR, "Error"),
    )

    STATE_BADGES = {
        STATE.NEW: "light",
        STATE.ACTIVE: "info",
        STATE.SUCCESS: "primary",
        STATE.CANCELED: "warning",
        STATE.ERROR: "danger",
    }

    name = models.CharField(max_length=128)
    state = FSMField(default=STATE.NEW, choices=STATE_CHOICES)

    def __str__(self):
        return self.name

    @transition(
        field=state,
        source=STATE.NEW,
        target=STATE.ACTIVE,
        on_error=STATE.ERROR,
        custom={"label": "Activate", "comment": WorkflowMixin.Comment.NONE},
    )
    def wf_activate(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=STATE.ACTIVE,
        target=STATE.SUCCESS,
        on_error=STATE.ERROR,
        custom={"label": "Done", "comment": WorkflowMixin.Comment.OPTIONAL},
    )
    def wf_done(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=STATE.NEW,
        target=STATE.CANCELED,
        on_error=STATE.ERROR,
        custom={"label": "Cancel", "comment": WorkflowMixin.Comment.REQUIRED},
    )
    def wf_cancel_new(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=STATE.ACTIVE,
        target=STATE.CANCELED,
        on_error=STATE.ERROR,
        custom={"label": "Cancel", "comment": WorkflowMixin.Comment.REQUIRED},
    )
    def wf_cancel_active(self, request=None, by=None, comment=None):
        pass


class Vehicle(PolymorphicModel):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Car(Vehicle):
    doors = models.IntegerField(default=4)


class Truck(Vehicle):
    payload_tons = models.IntegerField(default=10)
