from nested.views import cv_company, cv_department, cv_employee, cv_office

urlpatterns = cv_company.urlpatterns + cv_department.urlpatterns + cv_employee.urlpatterns + cv_office.urlpatterns
