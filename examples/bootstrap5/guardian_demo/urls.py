from guardian_demo.views import cv_document, cv_note

urlpatterns = cv_document.urlpatterns + cv_note.urlpatterns
