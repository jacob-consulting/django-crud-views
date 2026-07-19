from django.urls import path

from breadcrumbs.views import HostView, cv_board, cv_workspace

urlpatterns = (
    [path("host/", HostView.as_view(), name="breadcrumbs-host")] + cv_workspace.urlpatterns + cv_board.urlpatterns
)
