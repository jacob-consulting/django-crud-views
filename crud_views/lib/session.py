from typing import Dict, Any

from pydantic import BaseModel, Field

from crud_views.lib.settings import crud_views_settings


def default_dict(*args, **kwargs) -> Any:
    return dict()


class ViewData(BaseModel):
    data: Dict[str, Any] = Field(default_factory=default_dict)  # cv_key to Any

    def set(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key)


class ViewSetData(BaseModel):
    views: Dict[str, ViewData] = Field(default_factory=default_dict)  # ViewSet name to ViewData

    def get_view_data(self, view_key: str) -> ViewData:
        if view_key not in self.views.keys():
            view_data = ViewData()
            self.views[view_key] = view_data
            return view_data
        return self.views[view_key]


class SessionData(BaseModel):
    """
    Session data for django-viewset.
    Data ist stored in a hierarchy: app -> viewset -> view -> data
    """
    view: Any = None
    apps: Dict[str, ViewSetData] = Field(default_factory=default_dict)  # app ViewSetData

    @property
    def view_key(self) -> str:
        key = f"{self.view.cv_viewset.name}-{self.view.cv_key}"
        return key

    @property
    def app_label(self) -> str:
        return self.view.model._meta.app_label

    def get_viewset_data(self) -> ViewSetData:
        if self.app_label not in self.apps.keys():
            viewset_data = ViewSetData()
            self.apps[self.app_label] = viewset_data
            return viewset_data
        return self.apps[self.app_label]

    def get_view_data(self) -> ViewData:
        viewset = self.get_viewset_data()
        return viewset.get_view_data(self.view_key)

    @classmethod
    def from_view(cls, view):
        session_data = view.request.session.get(crud_views_settings.session_data_key, None)
        if session_data is None:
            session_data = SessionData(view=view)
        else:
            session_data = SessionData(view=view, **session_data)
        return session_data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        serialized_data = self.model_dump(exclude={"view",})
        self.view.request.session[crud_views_settings.session_data_key] = serialized_data

    def __setitem__(self, key: str, value: Any):
        data = self.get_view_data()
        data.data[key] = value

    def __getitem__(self, key: str) -> Any:
        data = self.get_view_data()
        return data.data[key]

    def __delitem__(self, key: str):
        data = self.get_view_data()
        del data.data[key]

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default
