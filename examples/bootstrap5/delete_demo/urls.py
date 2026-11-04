from delete_demo.views import cv_project, cv_task

urlpatterns = cv_project.urlpatterns + cv_task.urlpatterns
