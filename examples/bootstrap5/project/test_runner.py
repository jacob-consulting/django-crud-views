from django.conf import settings
from django.test.runner import DiscoverRunner


class BaseDirDiscoverRunner(DiscoverRunner):
    """Pin test discovery's top-level directory to ``BASE_DIR``.

    ``manage.py test app`` otherwise discovers with the top-level directory set to
    the ``app/`` package itself, so unittest imports the app's sub-packages under
    non-canonical names (e.g. ``views.formset`` instead of ``app.views.formset``).

    Several view packages register a ViewSet at import time in their
    ``__init__.py`` (``app/views/formset``, ``app/views/poly``). The non-canonical
    import executes that ``__init__`` once, then the canonical import from
    ``app.urls`` executes it again under a different module name — registering the
    same ViewSet twice and tripping the duplicate-name guard
    (``ViewSetError: ViewSet name poly_formset is already registered``).

    Pinning the top-level directory to ``BASE_DIR`` makes both imports resolve to
    the same canonical module name, so each package ``__init__`` runs once.
    An explicit ``-t/--top-level-directory`` on the command line still wins.
    """

    def __init__(self, *args, top_level=None, **kwargs):
        if top_level is None:
            top_level = str(settings.BASE_DIR)
        super().__init__(*args, top_level=top_level, **kwargs)
