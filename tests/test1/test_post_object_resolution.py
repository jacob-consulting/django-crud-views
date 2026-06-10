"""
Audit H2: create/update/delete POST handling must not use a swallowed
AttributeError to decide between create and update. A genuine error inside
get_object() (e.g. a typo in a custom queryset) must propagate instead of
silently running the create path.
"""

import pytest
from django import forms
from django.test.client import RequestFactory

from tests.test1.app.models import Publisher


@pytest.mark.django_db
def test_update_post_propagates_get_object_errors(user_publisher_formset):
    from tests.test1.app.views_formset import PublisherFormSetUpdateView

    class BrokenUpdateView(PublisherFormSetUpdateView):
        def get_object(self, queryset=None):
            raise AttributeError("broken queryset")

    publisher = Publisher.objects.create(name="Saga")
    request = RequestFactory().post(f"/publisher-formset/{publisher.pk}/update/", {"name": "Changed"})
    request.user = user_publisher_formset

    with pytest.raises(AttributeError, match="broken queryset"):
        BrokenUpdateView.as_view()(request, pk=publisher.pk)

    # and no phantom object was created by a silent create path
    assert Publisher.objects.count() == 1


@pytest.mark.django_db
def test_delete_post_propagates_get_object_errors(user_publisher_delete):
    from tests.test1.app.views import PublisherDeleteView

    class BrokenDeleteView(PublisherDeleteView):
        def get_object(self, queryset=None):
            raise AttributeError("broken queryset")

    publisher = Publisher.objects.create(name="Saga")
    request = RequestFactory().post(f"/publisher/{publisher.pk}/delete/", {"confirm": True})
    request.user = user_publisher_delete

    with pytest.raises(AttributeError, match="broken queryset"):
        BrokenDeleteView.as_view()(request, pk=publisher.pk)

    assert Publisher.objects.filter(pk=publisher.pk).exists()


@pytest.mark.django_db
def test_custom_form_no_object_view_posts_without_object(user_publisher_formset):
    """A no-object form view must take the object=None path structurally."""
    from crud_views.lib.views.form import CustomFormNoObjectView
    from tests.test1.app.views_formset import cv_publisher_formset

    class ContactForm(forms.Form):
        message = forms.CharField()

    class NoObjectContactView(CustomFormNoObjectView):
        cv_viewset = cv_publisher_formset
        cv_key = "contact"
        cv_path = "contact"
        cv_backend_only = True
        form_class = ContactForm

    request = RequestFactory().post("/publisher-formset/contact/", {"message": "hi"})
    request.user = user_publisher_formset

    response = NoObjectContactView.as_view()(request)
    assert response.status_code == 302
