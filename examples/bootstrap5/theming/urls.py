from django.urls import path

from theming.views import ThemeIndexView

urlpatterns = [path("", ThemeIndexView.as_view(), name="theming-index")]
