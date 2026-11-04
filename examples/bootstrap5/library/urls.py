from library.views import cv_author, cv_book, cv_contract

urlpatterns = cv_author.urlpatterns + cv_book.urlpatterns + cv_contract.urlpatterns
