from django.urls import path

# Minimal URL patterns for reverse() in the ported object-detail resolver tests.

urlpatterns = [
    path("reports/<int:pk>/", lambda r, pk: None, name="report-detail"),
    path("reports/<int:report_id>/", lambda r, report_id: None, name="report-by-id"),
    path("users/<int:pk>/", lambda r, pk: None, name="user-detail"),
    path("info/<int:pk>/", lambda r, pk: None, name="info-detail"),
]
