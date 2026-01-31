"""
Litestar implementation of the AppIntrospector interface.

This module provides the adapter that allows fastapi-voyager to work with Litestar applications.
"""
from collections.abc import Iterator

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
                # Skip routes without path or methods
                if not hasattr(route, "path") or not hasattr(route, "methods"):
                    continue

                # Skip Litestar's auto-generated schema routes
                if hasattr(route, "path") and route.path.startswith("/schema"):
                    continue

                # Get the handler function from route_handlers
                handler = None
                handler_obj = None
                if hasattr(route, "route_handlers") and route.route_handlers:
                    # Find the GET handler (or any non-OPTIONS handler)
                    for route_handler in route.route_handlers:
                        if hasattr(route_handler, "fn") and hasattr(route_handler.fn, "__name__"):
                            # Store the route handler object for tags
                            if hasattr(route_handler, "http_methods") and "GET" in route_handler.http_methods:
                                handler_obj = route_handler
                            handler = route_handler.fn
                            if handler_obj:
                                break

                if not handler:
                    continue

                # Skip handlers with names starting with _ (internal/private)
                if hasattr(handler, "__name__") and handler.__name__.startswith("_"):
                    continue

                # Extract tags from the route handler object
                tags = []
                if handler_obj and hasattr(handler_obj, "tags") and handler_obj.tags:
                    tags = list(handler_obj.tags)

                # Get return type from handler's annotations
                return_model = type(None)
                if hasattr(handler, "__annotations__") and "return" in handler.__annotations__:
                    return_model = handler.__annotations__["return"]

                yield RouteInfo(
                    id=self._get_route_id(handler),
                    name=handler.__name__,
                    module=handler.__module__,
                    operation_id=self._get_operation_id(route, handler),
                    tags=tags,
                    endpoint=handler,
                    response_model=return_model,
                    extra={
                        "methods": list(route.methods) if hasattr(route, "methods") else [],
                        "path": route.path,
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

    def _get_operation_id(self, route, handler) -> str:
        """
        Extract or generate the operation ID for the route.

        Args:
            route: The Litestar route object
            handler: The handler function

        Returns:
            An operation ID string
        """
        # Litestar might not have operation_id, so we generate one
        if hasattr(route, "operation_id"):
            return route.operation_id
        # Fallback to using the handler function name
        if hasattr(handler, "__name__"):
            return handler.__name__
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
