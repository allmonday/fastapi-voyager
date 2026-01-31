import os
import django
from django.core.asgi import get_asgi_application

# Configure Django settings before importing django-ninja
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.django_ninja.settings')
django.setup()

from fastapi_voyager import create_voyager
from tests.django_ninja.demo import api, diagram

# Create the voyager app
voyager_app = create_voyager(
    api,
    er_diagram=diagram,
    module_color={"tests.service": "purple"},
    module_prefix="tests.service",
    swagger_url="/api/docs",  # Django Ninja's swagger URL
    initial_page_policy='first',
    ga_id='G-R64S7Q49VL',
    online_repo_url="https://github.com/allmonday/fastapi-voyager/blob/main",
    enable_pydantic_resolve_meta=True
)


async def application(scope, receive, send):
    """
    ASGI application that routes between Django and Voyager.
    """
    # Route /voyager/* to voyager_app, everything else to Django
    if scope['type'] == 'http' and scope['path'].startswith('/voyager'):
        # Update path for voyager app (remove /voyager prefix)
        new_scope = dict(scope)
        new_scope['path'] = scope['path'][8:]  # Remove '/voyager'
        if new_scope['path'] == '':
            new_scope['path'] = '/'
        # Update raw_path as well if it exists
        if 'raw_path' in new_scope:
            new_scope['raw_path'] = scope['raw_path'][8:]
        return await voyager_app(new_scope, receive, send)
    else:
        # Pass everything else to Django's ASGI application
        django_asgi_app = get_asgi_application()
        return await django_asgi_app(scope, receive, send)


# Export app for uvicorn
app = application
