from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Assign per-object guardian permissions to demo users for the guardian example."

    def handle(self, *args, **options):
        from app.models import Author, Book
        from app.views.author import cv_author
        from app.views.book import cv_book

        User = get_user_model()

        manage_group, _ = Group.objects.get_or_create(name="CRUD_VIEWS_MANAGE")

        editor, _ = User.objects.get_or_create(username="editor")
        editor.set_password("editor")
        editor.save()
        editor.groups.add(manage_group)

        reader, _ = User.objects.get_or_create(username="reader")
        reader.set_password("reader")
        reader.save()
        reader.groups.add(manage_group)

        # Give editor model-level add_author so top-level create works
        ct = ContentType.objects.get_for_model(Author)
        add_perm = Permission.objects.get(content_type=ct, codename="add_author")
        editor.user_permissions.add(add_perm)

        for author in Author.objects.all():
            cv_author.assign_perm("view", reader, author)
            cv_author.assign_perm("view", editor, author)
            cv_author.assign_perm("change", editor, author)
            cv_author.assign_perm("delete", editor, author)

        for book in Book.objects.all():
            cv_book.assign_perm("view", reader, book)
            cv_book.assign_perm("view", editor, book)
            cv_book.assign_perm("change", editor, book)
            cv_book.assign_perm("delete", editor, book)

        self.stdout.write(
            self.style.SUCCESS(
                "Done. Users: editor/editor (full access), reader/reader (view only).\n"
                "Both users are members of CRUD_VIEWS_MANAGE — manage views accessible.\n"
                "Run 'python manage.py loaddata authors' first if no authors exist."
            )
        )
