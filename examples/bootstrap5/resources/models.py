from django.db import models


class S3FilePermissions(models.Model):
    """
    Permission holder for the S3File Resource demo: unmanaged, no table —
    exists only so ContentType/Permission rows are created.
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ("view_s3file", "Can view S3 files"),
            ("delete_s3file", "Can delete S3 files"),
        ]
