from conditional.views import cv_customer, cv_event, cv_registration

urlpatterns = cv_registration.urlpatterns + cv_event.urlpatterns + cv_customer.urlpatterns
