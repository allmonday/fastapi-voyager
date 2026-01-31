"""
URL configuration for django-ninja test app.
"""
from django.urls import path

from tests.django_ninja.demo import api

urlpatterns = [
    path('api/', api.urls),
]
