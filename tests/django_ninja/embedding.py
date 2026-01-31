"""
Django Ninja embedding example for fastapi-voyager.

This module demonstrates how to integrate voyager with a Django Ninja application.
"""
import os

import django
from django.core.asgi import get_asgi_application

# Configure Django settings before importing django-ninja
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_ninja.settings")
django.setup()

from fastapi_voyager import create_voyager
from tests.django_ninja.demo import api, diagram

# Create the voyager ASGI application
# Note: create_voyager automatically detects Django Ninja and returns an ASGI app
voyager_asgi_app = create_voyager(
    api,
    er_diagram=diagram,
    module_color={"tests.service": "purple"},
    module_prefix="tests.service",
    swagger_url="/api/docs",  # Django Ninja's swagger URL
    initial_page_policy="first",
    ga_id="G-R64S7Q49VL",
    online_repo_url="https://github.com/allmonday/fastapi-voyager/blob/main",
    enable_pydantic_resolve_meta=True,
)


async def application(scope, receive, send):
    """
    ASGI application that routes between Django and Voyager.

    This is a simple router that:
    - Sends /voyager/* requests to the voyager UI
    - Sends everything else to Django

    For production, you might want to use Django's URL routing instead.
    """
    # Route /voyager/* to voyager_app
    if scope["type"] == "http" and scope["path"].startswith("/voyager"):
        return await voyager_asgi_app(scope, receive, send)
    else:
        # Pass everything else to Django's ASGI application
        django_asgi_app = get_asgi_application()
        return await django_asgi_app(scope, receive, send)


# Export app for uvicorn
app = application


# ALTERNATIVE: Integration with Django URLs
# ==========================================
# If you prefer to integrate voyager through Django's URL system,
# you can use the following approach in your Django project's urls.py:
#
# from django.urls import path
# from tests.django_ninja.embedding import voyager_asgi_app
#
# def voyager_wrapper(request):
#     '''Wrap voyager ASGI app for Django'''
#     async def asgi_wrapper(receive, send):
#         scope = {
#             'type': 'http',
#             'asgi': {'version': '3.0'},
#             'http_method': request.method,
#             'path': request.path.replace('/voyager', '') or '/',
#             'query_string': request.META.get('QUERY_STRING', '').encode(),
#             'headers': [
#                 (k.lower().encode(), v.encode())
#                 for k, v in request.META.items()
#                 if k.startswith('HTTP_')
#             ],
#         }
#         await voyager_asgi_app(scope, receive, send)
#
#     return asgi_wrapper
#
# urlpatterns = [
#     path('voyager/', voyager_wrapper),
#     # ... other URL patterns
# ]
