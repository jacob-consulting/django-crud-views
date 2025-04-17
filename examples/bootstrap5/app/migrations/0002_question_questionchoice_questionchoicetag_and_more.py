# Generated by Django 5.1.7 on 2025-04-17 18:25

import app.models.questions
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Question",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "question",
                    models.CharField(
                        max_length=100,
                        validators=[app.models.questions.validate_questionmark],
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="QuestionChoice",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "order",
                    models.PositiveIntegerField(
                        db_index=True, editable=False, verbose_name="order"
                    ),
                ),
                (
                    "choice",
                    models.CharField(
                        max_length=100, validators=[app.models.questions.validate_alpha]
                    ),
                ),
                ("help_text", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="app.question"
                    ),
                ),
            ],
            options={
                "ordering": ("order",),
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="QuestionChoiceTag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "order",
                    models.PositiveIntegerField(
                        db_index=True, editable=False, verbose_name="order"
                    ),
                ),
                ("tag", models.CharField(max_length=100)),
                (
                    "choice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="app.questionchoice",
                    ),
                ),
            ],
            options={
                "ordering": ("order",),
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="QuestionChoiceTagAnnotation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "order",
                    models.PositiveIntegerField(
                        db_index=True, editable=False, verbose_name="order"
                    ),
                ),
                ("annotation", models.CharField(max_length=100)),
                (
                    "tag",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="app.questionchoicetag",
                    ),
                ),
            ],
            options={
                "ordering": ("order",),
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="QuestionTag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("tag", models.CharField(max_length=100)),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="app.question"
                    ),
                ),
            ],
        ),
    ]
