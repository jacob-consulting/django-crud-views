from crud_views.lib.settings import crud_views_settings


def crud_views_context(request) -> dict:  # NOSONAR S1172: Django context-processor signature
    data = crud_views_settings.as_dict
    return data
