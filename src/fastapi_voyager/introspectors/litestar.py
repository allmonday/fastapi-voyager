"""
Litestar implementation of the AppIntrospector interface.

This module provides the adapter that allows fastapi-voyager to work with Litestar applications.
"""
from typing import Iterator

from fastapi_voyager.introspectors.base import AppIntrospector, RouteInfo


class LitestarIntrospector(AppIntrospector):
    """
    Litestar-specific implementation of AppIntrospector.

    This class extracts route information from Litestar's internal structure
    and converts it to the framework-agnostic RouteInfo format.
    """

    def __init__(self, app, swagger_url: str | None = None):
        """
        Initialize the Litestar introspector.

        Args:
            app: The Litestar application instance
            swagger_url: Optional custom URL to Swagger/OpenAPI documentation
        """
        self.app = app
        self.swagger_url = swagger_url or "/schema/swagger"

    def get_routes(self) -> Iterator[RouteInfo]:
        """
        Iterate over all routes in the Litestar application.

        Yields:
            RouteInfo: Standardized route information for each route
        """
        for route in self.app.routes:
            try:
                # Skip routes that don't have a handler
                if not hasattr(route, "handler"):
                    continue

                handler = route.handler
                if not handler:
                    continue

                # Extract tags from route
                tags = []
                if hasattr(route, "tags"):
                    tags = list(route.tags) if route.tags else []

                yield RouteInfo(
                    id=self._get_route_id(handler),
                    name=handler.__name__,
                    module=handler.__module__,
                    operation_id=self._get_operation_id(route),
                    tags=tags,
                    endpoint=handler,
                    response_model=self._get_response_model(route),
                    extra={
                        "methods": list(route.http_methods) if hasattr(route, "http_methods") else [],
                        "path": route.path if hasattr(route, "path") else "",
                    },
                )
            except (AttributeError, TypeError):
                # Skip routes that don't have the expected structure
                continue

    def get_swagger_url(self) -> str | None:
        """
        Get the URL to the Swagger/OpenAPI documentation.

        Returns:
            The URL path to Swagger UI
        """
        return self.swagger_url

    def _get_route_id(self, handler) -> str:
        """
        Generate a unique identifier for the route.

        Uses the full module path of the handler function.

        Args:
            handler: The route handler function

        Returns:
            A unique identifier string
        """
        # Import here to avoid circular dependency
        from fastapi_voyager.type_helper import full_class_name
        return full_class_name(handler)

    def _get_operation_id(self, route) -> str:
        """
        Extract or generate the operation ID for the route.

        Args:
            route: The Litestar route object

        Returns:
            An operation ID string
        """
        # Litestar might not have operation_id, so we generate one
        if hasattr(route, "operation_id"):
            return route.operation_id
        # Fallback to using the path
        if hasattr(route, "path"):
            return route.path
        return ""

    def _get_response_model(self, route) -> type:
        """
        Extract the response model from the route.

        Args:
            route: The Litestar route object

        Returns:
            The response model class
        """
        # Try to get response model from route
        if hasattr(route, "responses"):
            responses = route.responses
            if responses and "200" in responses:
                response_200 = responses["200"]
                if hasattr(response_200, "model"):
                    return response_200.model

        # Fallback: check if handler has return annotation
        handler = route.handler if hasattr(route, "handler") else None
        if handler and hasattr(handler, "__annotations__") and "return" in handler.__annotations__:
            return handler.__annotations__["return"]

        # Return None if no response model found
        return type(None)  # type: ignore
