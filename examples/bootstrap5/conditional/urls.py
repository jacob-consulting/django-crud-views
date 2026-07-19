from conditional.views import cv_event, cv_registration

urlpatterns = cv_registration.urlpatterns + cv_event.urlpatterns
