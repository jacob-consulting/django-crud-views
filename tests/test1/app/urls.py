from tests.test1.app.views import (
    cv_author,
    cv_author_wide_card,
    cv_author_custom_detail,
    cv_publisher,
    cv_publisher_order,
    cv_book,
    cv_contract,
    cv_vehicle,
    cv_campaign,
    cv_guardian_author,
    cv_guardian_publisher,
    cv_guardian_book,
    cv_guardian_publisher_cascade,
    cv_publisher_cascade,
    cv_publisher_protected,
    cv_publisher_form_protected,
    cv_publisher_linked,
    cv_author_modal,
    cv_publisher_modal_protected,
    cv_publisher_bc,
    cv_publisher_bc_nodetail,
    cv_publisher_bc_card,
    cv_book_bc,
    cv_booknote_bc,
)
from tests.test1.app.views_formset import cv_publisher_formset
from tests.test1.app.resources import cv_s3file, cv_publisher_file

urlpatterns = []
urlpatterns += cv_author.urlpatterns
urlpatterns += cv_author_wide_card.urlpatterns
urlpatterns += cv_author_custom_detail.urlpatterns
urlpatterns += cv_publisher.urlpatterns
urlpatterns += cv_publisher_order.urlpatterns
urlpatterns += cv_book.urlpatterns
urlpatterns += cv_contract.urlpatterns
urlpatterns += cv_vehicle.urlpatterns
urlpatterns += cv_campaign.urlpatterns
urlpatterns += cv_guardian_author.urlpatterns
urlpatterns += cv_guardian_publisher.urlpatterns
urlpatterns += cv_guardian_book.urlpatterns
urlpatterns += cv_guardian_publisher_cascade.urlpatterns
urlpatterns += cv_publisher_cascade.urlpatterns
urlpatterns += cv_publisher_protected.urlpatterns
urlpatterns += cv_publisher_form_protected.urlpatterns
urlpatterns += cv_publisher_linked.urlpatterns
urlpatterns += cv_publisher_formset.urlpatterns
urlpatterns += cv_author_modal.urlpatterns
urlpatterns += cv_publisher_modal_protected.urlpatterns
urlpatterns += cv_s3file.urlpatterns
urlpatterns += cv_publisher_file.urlpatterns
urlpatterns += cv_publisher_bc.urlpatterns
urlpatterns += cv_publisher_bc_nodetail.urlpatterns
urlpatterns += cv_publisher_bc_card.urlpatterns
urlpatterns += cv_book_bc.urlpatterns
urlpatterns += cv_booknote_bc.urlpatterns
