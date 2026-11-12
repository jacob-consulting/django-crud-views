from formsets.views import cv_checklist, cv_questionnaire

urlpatterns = [*cv_questionnaire.urlpatterns, *cv_checklist.urlpatterns]
