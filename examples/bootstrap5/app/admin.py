from django.contrib import admin

from app.models import Author


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "pseudonym", "created_dt", "modified_dt"]
