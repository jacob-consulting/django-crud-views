"""URLconf of the public demo: the local URLconf without the Django admin."""

from project.urls import urlpatterns as _local_urlpatterns

urlpatterns = [p for p in _local_urlpatterns if str(p.pattern) != "admin/"]
