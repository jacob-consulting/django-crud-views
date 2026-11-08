import uuid

from django.db import models
from django.utils.translation import gettext as _
from django_fsm import FSMField, transition
from ordered_model.models import OrderedModel
from polymorphic.models import PolymorphicModel

from crud_views_workflow.lib.enums import BadgeEnum, WorkflowComment
from crud_views_workflow.lib.mixins import WorkflowModelMixin


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

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PublisherProxy(Publisher):
    """Exercise the proxy-root content-type mode of the Guardian label lookup."""

    class Meta:
        proxy = True


class Book(models.Model):
    title = models.CharField(max_length=200)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="books")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Genre(models.Model):
    """M2M child of Publisher: exercises CreateViewParentMixin's many_to_many_through branch."""

    name = models.CharField(max_length=100)
    publishers = models.ManyToManyField(Publisher, related_name="genres")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class BookNote(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="notes")
    note = models.CharField(max_length=200)

    class Meta:
        ordering = ["note"]

    def __str__(self):
        return self.note


class Contract(models.Model):
    publisher = models.ForeignKey(Publisher, on_delete=models.PROTECT, related_name="contracts")
    title = models.CharField(max_length=200)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Royalty(models.Model):
    """CR-01 protected-list model without a view_ permission; RESTRICT also exercises 06.2-08's write path."""

    publisher = models.ForeignKey(Publisher, on_delete=models.RESTRICT, related_name="royalties")
    title = models.CharField(max_length=100)

    class Meta:
        default_permissions = ("add", "change", "delete")

    def __str__(self):
        return self.title


class CampaignState(models.TextChoices):
    NEW = "new", _("New")
    ACTIVE = "active", _("Active")
    SUCCESS = "success", _("Success")
    CANCELED = "canceled", _("Cancelled")
    ERROR = "error", _("Error")


class Campaign(WorkflowModelMixin, models.Model):
    STATE_CHOICES = CampaignState
    STATE_BADGES = {
        CampaignState.NEW: BadgeEnum.LIGHT,
        CampaignState.ACTIVE: BadgeEnum.INFO,
        CampaignState.SUCCESS: BadgeEnum.PRIMARY,
        CampaignState.CANCELED: BadgeEnum.WARNING,
        CampaignState.ERROR: BadgeEnum.DANGER,
    }

    name = models.CharField(max_length=128)
    state = FSMField(default=CampaignState.NEW, choices=CampaignState.choices)

    def __str__(self):
        return self.name

    @transition(
        field=state,
        source=CampaignState.NEW,
        target=CampaignState.ACTIVE,
        on_error=CampaignState.ERROR,
        custom={"label": "Activate", "comment": WorkflowComment.NONE},
    )
    def wf_activate(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=CampaignState.ACTIVE,
        target=CampaignState.SUCCESS,
        on_error=CampaignState.ERROR,
        custom={"label": "Done", "comment": WorkflowComment.OPTIONAL},
    )
    def wf_done(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=CampaignState.NEW,
        target=CampaignState.CANCELED,
        on_error=CampaignState.ERROR,
        custom={"label": "Cancel", "comment": WorkflowComment.REQUIRED},
    )
    def wf_cancel_new(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=CampaignState.ACTIVE,
        target=CampaignState.CANCELED,
        on_error=CampaignState.ERROR,
        custom={"label": "Cancel", "comment": WorkflowComment.REQUIRED},
    )
    def wf_cancel_active(self, request=None, by=None, comment=None):
        pass


class WorkflowRequestState(models.TextChoices):
    NEW = "new", _("New")
    PROCESSED = "processed", _("Processed")
    CANCELED = "canceled", _("Canceled")


class WorkflowRequest(WorkflowModelMixin, models.Model):
    STATE_CHOICES = WorkflowRequestState
    STATE_BADGES = {
        WorkflowRequestState.NEW: BadgeEnum.LIGHT,
        WorkflowRequestState.PROCESSED: BadgeEnum.PRIMARY,
        WorkflowRequestState.CANCELED: BadgeEnum.WARNING,
    }

    name = models.CharField(max_length=128)
    state = FSMField(default=WorkflowRequestState.NEW, choices=WorkflowRequestState.choices)

    class Meta:
        permissions = [("process_workflowrequest", "Can process workflow request")]

    def __str__(self):
        return self.name

    @transition(
        field=state,
        source=WorkflowRequestState.NEW,
        target=WorkflowRequestState.PROCESSED,
        permission="app.process_workflowrequest",
        custom={"label": "Process", "comment": WorkflowComment.NONE},
    )
    def wf_process(self, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=WorkflowRequestState.NEW,
        target=WorkflowRequestState.CANCELED,
        permission="app.change_workflowrequest",
        custom={"label": "Cancel", "comment": WorkflowComment.NONE},
    )
    def wf_cancel(self, by=None, comment=None):
        pass


class Vehicle(PolymorphicModel):
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Car(Vehicle):
    doors = models.IntegerField(default=4)


class Truck(Vehicle):
    payload_tons = models.IntegerField(default=10)


class S3FilePermissions(models.Model):
    """
    Permission holder for the S3File Resource (spec §7): unmanaged, no table,
    no default permissions — exists only so ContentType/Permission rows are
    created for the custom permissions below.
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ("view_s3file", "Can view S3 files"),
            ("delete_s3file", "Can delete S3 files"),
        ]


class Profile(models.Model):
    name = models.CharField(max_length=100)
    with_contact = models.BooleanField(default=False)
    with_items = models.BooleanField(default=False)
    email = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


class ProfileItem(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="items")
    label = models.CharField(max_length=100)

    def __str__(self):
        return self.label


class ConditionalPersistenceRecord(models.Model):
    """Schema-backed conditional persistence fixture; no product migration."""

    parent = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="conditional_records")
    active = models.BooleanField(default=False)
    nullable_text = models.CharField(max_length=100, null=True, blank=True, default="default text")
    blank_text = models.CharField(max_length=100, blank=True, default="default text")
    unique_text = models.CharField(max_length=100, blank=True, null=True, unique=True)
    flag = models.BooleanField(default=True)
    nullable_flag = models.BooleanField(null=True, blank=True, default=True)
    number = models.IntegerField(null=True, blank=True, default=42)
    decimal = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    token = models.UUIDField(null=True, blank=True)
    reference = models.ForeignKey(Publisher, null=True, blank=True, on_delete=models.SET_NULL)
    attachment = models.FileField(upload_to="conditional/", blank=True)
    image = models.ImageField(upload_to="conditional/", blank=True)
    tags = models.ManyToManyField(Publisher, blank=True, related_name="conditional_tags")


class UUIDFragmentRow(models.Model):
    """Test-only UUID-keyed inline row of an Author (formset fragment ancestry, Phase 6.2 B2)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="fragment_rows")
    text = models.CharField(max_length=100)

    def __str__(self):
        return self.text


class UUIDFragmentLeaf(models.Model):
    """Test-only inline leaf of a UUIDFragmentRow (nested formset fragment ancestry, Phase 6.2 B2)."""

    row = models.ForeignKey(UUIDFragmentRow, on_delete=models.CASCADE, related_name="leaves")
    text = models.CharField(max_length=100)

    def __str__(self):
        return self.text


class AncestorAttachment(models.Model):
    """Test-only leaf of BookNote: the deepest level of the Publisher → Book → BookNote → attachment ancestry chain."""

    note = models.ForeignKey(BookNote, on_delete=models.CASCADE, related_name="ancestor_attachments")
    text = models.CharField(max_length=100)

    def __str__(self):
        return self.text
