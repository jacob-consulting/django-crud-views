from object_detail.views import cv_product, cv_supplier

urlpatterns = cv_product.urlpatterns + cv_supplier.urlpatterns
