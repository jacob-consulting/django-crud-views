from django.core.checks import Tags as DjangoTags
from django.core.checks import register

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.viewset import ViewSet


class Tags(DjangoTags):
    """Do this if none of the existing tags work for you:
    https://docs.djangoproject.com/en/1.8/ref/checks/#builtin-tags
    """
    my_new_tag = 'my_new_tag'


@register(Tags.my_new_tag)
def check_taggit_is_installed(app_configs=None, **kwargs):
    "Check that django-taggit is installed when usying myapp."

    errors = crud_views_settings.check_messages

    for check in ViewSet.checks_all():
        for message in check.messages():
            errors.append(message)
    return errors
