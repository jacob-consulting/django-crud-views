FFFF                                                                     [100%]
=================================== FAILURES ===================================
_____ test_proposed_catch_can_run_after_delete_commit[True-ProtectedError] _____

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x70c68bcd7e60>
error_type = <class 'django.db.models.deletion.ProtectedError'>, atomic = True

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize('error_type', [ProtectedError, RestrictedError])
    @pytest.mark.parametrize('atomic', [True, False])
    def test_proposed_catch_can_run_after_delete_commit(monkeypatch, error_type, atomic):
        publisher = Publisher.objects.create(name='Review callback probe')
        original_pk = publisher.pk
        view = PublisherDeleteView()
        view.object = publisher
        view.cv_atomic = atomic
        def callback(context):
            raise error_type('Callback encountered unrelated protected relationship', set())
        monkeypatch.setattr(view, 'cv_on_commit', callback)
        caught_as_blocked = False
        try:
>           view.cv_form_valid_process({})

/tmp/gsd-review-s_glfn1_/test_review_backstop.py:20: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/crud_views/lib/views/mixins.py:56: in cv_form_valid_process
    self.cv_form_valid_hook(context)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <tests.test1.app.views.PublisherDeleteView object at 0x70c68bbdedb0>
context = {}

    def cv_form_valid_hook(self, context: dict):
        super().cv_form_valid_hook(context)
        message = self.cv_get_message()
        if message:
>           messages.success(self.request, message)
                             ^^^^^^^^^^^^
E           AttributeError: 'PublisherDeleteView' object has no attribute 'request'

src/crud_views/lib/views/mixins.py:141: AttributeError
____ test_proposed_catch_can_run_after_delete_commit[True-RestrictedError] _____

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x70c68bb924e0>
error_type = <class 'django.db.models.deletion.RestrictedError'>, atomic = True

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize('error_type', [ProtectedError, RestrictedError])
    @pytest.mark.parametrize('atomic', [True, False])
    def test_proposed_catch_can_run_after_delete_commit(monkeypatch, error_type, atomic):
        publisher = Publisher.objects.create(name='Review callback probe')
        original_pk = publisher.pk
        view = PublisherDeleteView()
        view.object = publisher
        view.cv_atomic = atomic
        def callback(context):
            raise error_type('Callback encountered unrelated protected relationship', set())
        monkeypatch.setattr(view, 'cv_on_commit', callback)
        caught_as_blocked = False
        try:
>           view.cv_form_valid_process({})

/tmp/gsd-review-s_glfn1_/test_review_backstop.py:20: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/crud_views/lib/views/mixins.py:56: in cv_form_valid_process
    self.cv_form_valid_hook(context)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <tests.test1.app.views.PublisherDeleteView object at 0x70c68ba1a510>
context = {}

    def cv_form_valid_hook(self, context: dict):
        super().cv_form_valid_hook(context)
        message = self.cv_get_message()
        if message:
>           messages.success(self.request, message)
                             ^^^^^^^^^^^^
E           AttributeError: 'PublisherDeleteView' object has no attribute 'request'

src/crud_views/lib/views/mixins.py:141: AttributeError
____ test_proposed_catch_can_run_after_delete_commit[False-ProtectedError] _____

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x70c68bb1cef0>
error_type = <class 'django.db.models.deletion.ProtectedError'>, atomic = False

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize('error_type', [ProtectedError, RestrictedError])
    @pytest.mark.parametrize('atomic', [True, False])
    def test_proposed_catch_can_run_after_delete_commit(monkeypatch, error_type, atomic):
        publisher = Publisher.objects.create(name='Review callback probe')
        original_pk = publisher.pk
        view = PublisherDeleteView()
        view.object = publisher
        view.cv_atomic = atomic
        def callback(context):
            raise error_type('Callback encountered unrelated protected relationship', set())
        monkeypatch.setattr(view, 'cv_on_commit', callback)
        caught_as_blocked = False
        try:
>           view.cv_form_valid_process({})

/tmp/gsd-review-s_glfn1_/test_review_backstop.py:20: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/crud_views/lib/views/mixins.py:56: in cv_form_valid_process
    self.cv_form_valid_hook(context)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <tests.test1.app.views.PublisherDeleteView object at 0x70c68ba186b0>
context = {}

    def cv_form_valid_hook(self, context: dict):
        super().cv_form_valid_hook(context)
        message = self.cv_get_message()
        if message:
>           messages.success(self.request, message)
                             ^^^^^^^^^^^^
E           AttributeError: 'PublisherDeleteView' object has no attribute 'request'

src/crud_views/lib/views/mixins.py:141: AttributeError
____ test_proposed_catch_can_run_after_delete_commit[False-RestrictedError] ____

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x70c68ba7ad50>
error_type = <class 'django.db.models.deletion.RestrictedError'>, atomic = False

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize('error_type', [ProtectedError, RestrictedError])
    @pytest.mark.parametrize('atomic', [True, False])
    def test_proposed_catch_can_run_after_delete_commit(monkeypatch, error_type, atomic):
        publisher = Publisher.objects.create(name='Review callback probe')
        original_pk = publisher.pk
        view = PublisherDeleteView()
        view.object = publisher
        view.cv_atomic = atomic
        def callback(context):
            raise error_type('Callback encountered unrelated protected relationship', set())
        monkeypatch.setattr(view, 'cv_on_commit', callback)
        caught_as_blocked = False
        try:
>           view.cv_form_valid_process({})

/tmp/gsd-review-s_glfn1_/test_review_backstop.py:20: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/crud_views/lib/views/mixins.py:56: in cv_form_valid_process
    self.cv_form_valid_hook(context)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <tests.test1.app.views.PublisherDeleteView object at 0x70c68ba7af90>
context = {}

    def cv_form_valid_hook(self, context: dict):
        super().cv_form_valid_hook(context)
        message = self.cv_get_message()
        if message:
>           messages.success(self.request, message)
                             ^^^^^^^^^^^^
E           AttributeError: 'PublisherDeleteView' object has no attribute 'request'

src/crud_views/lib/views/mixins.py:141: AttributeError
=========================== short test summary info ============================
FAILED ../../../../../tmp/gsd-review-s_glfn1_/test_review_backstop.py::test_proposed_catch_can_run_after_delete_commit[True-ProtectedError]
FAILED ../../../../../tmp/gsd-review-s_glfn1_/test_review_backstop.py::test_proposed_catch_can_run_after_delete_commit[True-RestrictedError]
FAILED ../../../../../tmp/gsd-review-s_glfn1_/test_review_backstop.py::test_proposed_catch_can_run_after_delete_commit[False-ProtectedError]
FAILED ../../../../../tmp/gsd-review-s_glfn1_/test_review_backstop.py::test_proposed_catch_can_run_after_delete_commit[False-RestrictedError]
4 failed in 0.42s
