from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import include, path
from project.urls import urlpatterns as project_patterns


# Preserve the real navbar, home, authentication and every existing feature route.
# The app URL module arrives with the migration in the next task.
urlpatterns = list(project_patterns)
try:
    from queryset_conditional.standalone import cv_service_request
except ModuleNotFoundError as exc:
    if exc.name != "queryset_conditional.standalone":
        raise
else:
    urlpatterns += [path("queryset-conditional/", include(cv_service_request.urlpatterns))]


@override_settings(ROOT_URLCONF=__name__)
class StandaloneRequestTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="request-admin", password="pw")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_authenticated_create_page_renders(self):
        response = self.client.get("/queryset-conditional/service-request/create/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="service"')
        self.assertContains(response, 'data-cv-toggle-queryset')
