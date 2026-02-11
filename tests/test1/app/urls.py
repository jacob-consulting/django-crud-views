from tests.test1.app.views import cv_author, cv_publisher, cv_book, cv_vehicle

urlpatterns = []
urlpatterns += cv_author.urlpatterns
urlpatterns += cv_publisher.urlpatterns
urlpatterns += cv_book.urlpatterns
urlpatterns += cv_vehicle.urlpatterns
