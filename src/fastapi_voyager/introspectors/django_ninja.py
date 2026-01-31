"""
Django Ninja implementation of the AppIntrospector interface.

This module provides the adapter that allows fastapi-voyager to work with Django Ninja applications.
"""
from collections.abc import Iterator

from fastapi_voyager.introspectors.base import AppIntrospector, RouteInfo


class DjangoNinjaIntrospector(AppIntrospector):
    """
    Django Ninja-specific implementation of AppIntrospector.

    This class extracts route information from Django Ninja's internal structure
    and converts it to the framework-agnostic RouteInfo format.
    """

    def __init__(self, ninja_api, swagger_url: str | None = None):
        """
        Initialize the Django Ninja introspector.

        Args:
            ninja_api: The Django Ninja API instance
            swagger_url: Optional custom URL to Swagger documentation
        """
        self.api = ninja_api
        self.swagger_url = swagger_url or "/api/docs"

    def get_routes(self) -> Iterator[RouteInfo]:
        """
        Iterate over all API routes in the Django Ninja application.

        Yields:
            RouteInfo: Standardized route information for each API route
        """
        # Access the internal router structure
        if not hasattr(self.api, "default_router"):
            return

        router = self.api.default_router

        # Iterate through all path operations registered in the router
        if not hasattr(router, "path_operations"):
            return

        for path, path_view in router.path_operations.items():
            # path_view is a PathView object with a list of operations
            if not hasattr(path_view, "operations"):
                continue

            for operation in path_view.operations:
                try:
                    yield RouteInfo(
                        id=self._get_route_id(operation),
                        name=operation.view_func.__name__,
                        module=operation.view_func.__module__,
                        operation_id=operation.operation_id or operation.view_func.__name__,
                        tags=operation.tags or [],
                        endpoint=operation.view_func,
                        response_model=self._get_response_model(operation),
                        extra={
                            "methods": operation.methods,  # This is a list
                            "path": path,
                        },
                    )
                except (AttributeError, TypeError):
                    # Skip routes that don't have the expected structure
                    continue

    def get_swagger_url(self) -> str | None:
        """
        Get the URL to the Swagger UI documentation.

        Returns:
            The URL path to Swagger UI
        """
        return self.swagger_url

    def _get_route_id(self, operation) -> str:
        """
        Generate a unique identifier for the route.

        Uses the full class path of the view function.

        Args:
            operation: The Django Ninja operation object

        Returns:
            A unique identifier string
        """
        # Import here to avoid circular dependency
        from fastapi_voyager.type_helper import full_class_name
        return full_class_name(operation.view_func)

    def _get_response_model(self, operation) -> type:
        """
        Extract the response model from the operation.

        Args:
            operation: The Django Ninja operation object

        Returns:
            The response model class
        """
        from ninja.constants import NOT_SET_TYPE

        # Django Ninja infers response model from function's return type annotation
        # Try to get it from the view function's annotations first
        if hasattr(operation.view_func, "__annotations__") and "return" in operation.view_func.__annotations__:
            return operation.view_func.__annotations__["return"]

        # Fallback to checking response_models (if explicitly set)
        if hasattr(operation, "response_models"):
            # Get the 200 response model, or the first one
            for status_code in [200, "200", "2xx"]:
                if status_code in operation.response_models:
                    model = operation.response_models[status_code]
                    if model is not NOT_SET_TYPE:
                        return model

        # Return None if no response model found
        return type(None)  # type: ignore
