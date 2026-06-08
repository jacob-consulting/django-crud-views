from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cvw", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="workflowinfo",
            old_name="workflow_object_id",
            new_name="workflow_object_pk",
        ),
        migrations.AlterField(
            model_name="workflowinfo",
            name="workflow_object_pk",
            field=models.CharField(max_length=255),
        ),
        migrations.AddIndex(
            model_name="workflowinfo",
            index=models.Index(
                fields=["workflow_object_pk", "workflow_object_content_type"],
                name="cvw_workflo_workflo_idx",
            ),
        ),
    ]
