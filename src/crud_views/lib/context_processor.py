from crud_views.lib.settings import crud_views_settings


def crud_views_context(request) -> dict:
    data = crud_views_settings.dict
    return data
