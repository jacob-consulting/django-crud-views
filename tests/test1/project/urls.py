from django.urls import path, include

urlpatterns = [
    path('', include('tests.test1.app.urls')),
]
