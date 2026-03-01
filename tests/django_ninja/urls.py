"""
URL configuration for django-ninja test app.
"""
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from tests.django_ninja import demo


def graphql_view(request):
    """统一处理 GET 和 POST 请求"""
    if request.method == 'GET':
        return demo.graphiql_playground(request)
    elif request.method == 'POST':
        return demo.graphql_endpoint(request)
    return demo.HttpResponse('Method not allowed', status=405)


urlpatterns = [
    path('api/', demo.api.urls),
    # GraphQL endpoints at root path
    path('graphql', csrf_exempt(graphql_view)),
    path('graphql/', csrf_exempt(graphql_view)),
    path('graphql/schema', demo.graphql_schema),
]
