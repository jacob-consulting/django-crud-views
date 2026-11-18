from django.urls import path

from navbar_demo.views import NavbarDemoHomeView, cv_address, cv_customer, cv_item, cv_order, cv_tenant

urlpatterns = [path("", NavbarDemoHomeView.as_view(), name="navbar-demo-home")]
urlpatterns += (
    cv_tenant.urlpatterns
    + cv_customer.urlpatterns
    + cv_order.urlpatterns
    + cv_item.urlpatterns
    + cv_address.urlpatterns
)
