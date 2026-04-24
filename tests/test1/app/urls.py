from tests.test1.app.views import (
    cv_author,
    cv_publisher,
    cv_book,
    cv_vehicle,
    cv_campaign,
    cv_guardian_author,
    cv_guardian_publisher,
    cv_guardian_book,
)

urlpatterns = []
urlpatterns += cv_author.urlpatterns
urlpatterns += cv_publisher.urlpatterns
urlpatterns += cv_book.urlpatterns
urlpatterns += cv_vehicle.urlpatterns
urlpatterns += cv_campaign.urlpatterns
urlpatterns += cv_guardian_author.urlpatterns
urlpatterns += cv_guardian_publisher.urlpatterns
urlpatterns += cv_guardian_book.urlpatterns
