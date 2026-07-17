from library.views import cv_author, cv_book

urlpatterns = cv_author.urlpatterns + cv_book.urlpatterns
