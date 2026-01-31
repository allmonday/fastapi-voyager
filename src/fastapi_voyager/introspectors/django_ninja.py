"""
Django Ninja implementation of the AppIntrospector interface.

This module provides the adapter that allows fastapi-voyager to work with Django Ninja applications.
"""
from typing import Iterator

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
        self.swagger_url = swagger_url or "/api/doc"

    def get_routes(self) -> Iterator[RouteInfo]:
        """
        Iterate over all API routes in the Django Ninja application.

        Yields:
            RouteInfo: Standardized route information for each API route
        """
        # Access the internal router structure
        if not hasattr(self.api, "_router"):
            return

        router = self.api._router

        # Iterate through all operations registered in the router
        for path, operations_dict in router.operations.items():
            for operation in operations_dict.values():
                try:
                    yield RouteInfo(
                        id=self._get_route_id(operation),
                        name=operation.view_func.__name__,
                        module=operation.view_func.__module__,
                        operation_id=operation.operation_id,
                        tags=operation.tags or [],
                        endpoint=operation.view_func,
                        response_model=self._get_response_model(operation),
                        extra={
                            "methods": [operation.method],
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
        if hasattr(operation, "response_model"):
            return operation.response_model
        # Fallback to checking the view function's return annotation
        if hasattr(operation.view_func, "__annotations__") and "return" in operation.view_func.__annotations__:
            return operation.view_func.__annotations__["return"]
        # Return None if no response model found
        return type(None)  # type: ignore
