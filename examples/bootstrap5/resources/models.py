from django.db import models
from django.utils.translation import gettext_lazy as _


class S3FilePermissions(models.Model):
    """
    Permission holder for the S3File Resource demo: unmanaged, no table —
    exists only so ContentType/Permission rows are created.
    """

    class Meta:
        managed = False
        verbose_name = _("S3 file")
        verbose_name_plural = _("S3 files")
        default_permissions = ()
        permissions = [
            ("view_s3file", _("Can view S3 files")),
            ("delete_s3file", _("Can delete S3 files")),
        ]
