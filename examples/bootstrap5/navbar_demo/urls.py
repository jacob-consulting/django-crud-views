from django.urls import path

from navbar_demo.views import NavbarDemoHomeView, cv_customer, cv_tenant

urlpatterns = [path("", NavbarDemoHomeView.as_view(), name="navbar-demo-home")]
urlpatterns += cv_tenant.urlpatterns + cv_customer.urlpatterns
