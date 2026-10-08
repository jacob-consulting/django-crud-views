from django.db import migrations, models


def null_pseudonym_to_empty(apps, schema_editor):
    apps.get_model("library", "Author").objects.filter(pseudonym__isnull=True).update(pseudonym="")


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0002_translatable_verbose_names"),
    ]

    operations = [
        migrations.RunPython(null_pseudonym_to_empty, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="author",
            name="pseudonym",
            field=models.CharField(blank=True, max_length=100, verbose_name="pseudonym"),
        ),
    ]
