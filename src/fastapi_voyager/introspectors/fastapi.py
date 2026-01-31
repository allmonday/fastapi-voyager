"""
FastAPI implementation of the AppIntrospector interface.

This module provides the adapter that allows fastapi-voyager to work with FastAPI applications.
"""
from collections.abc import Iterator

from fastapi import FastAPI, routing

from fastapi_voyager.introspectors.base import AppIntrospector, RouteInfo


class FastAPIIntrospector(AppIntrospector):
    """
    FastAPI-specific implementation of AppIntrospector.

    This class extracts route information from FastAPI's internal route structure
    and converts it to the framework-agnostic RouteInfo format.
    """

    def __init__(self, app: FastAPI, swagger_url: str | None = None):
        """
        Initialize the FastAPI introspector.

        Args:
            app: The FastAPI application instance
            swagger_url: Optional custom URL to Swagger documentation
        """
        self.app = app
        self.swagger_url = swagger_url or "/docs"

    def get_routes(self) -> Iterator[RouteInfo]:
        """
        Iterate over all API routes in the FastAPI application.

        Yields:
            RouteInfo: Standardized route information for each API route
        """
        for route in self.app.routes:
            # Only process APIRoute instances (not static files, etc.)
            if isinstance(route, routing.APIRoute):
                # Extract tags from the route
                tags = getattr(route, 'tags', None) or []

                yield RouteInfo(
                    id=self._get_route_id(route),
                    name=route.endpoint.__name__,
                    module=route.endpoint.__module__,
                    operation_id=route.operation_id,
                    tags=tags,
                    endpoint=route.endpoint,
                    response_model=route.response_model,
                    extra={
                        'unique_id': route.unique_id,
                        'methods': route.methods,
                        'path': route.path,
                    }
                )

    def get_swagger_url(self) -> str | None:
        """
        Get the URL to the Swagger UI documentation.

        Returns:
            The URL path to Swagger UI
        """
        return self.swagger_url

    def _get_route_id(self, route: routing.APIRoute) -> str:
        """
        Generate a unique identifier for the route.

        Uses the full class path of the endpoint function.

        Args:
            route: The FastAPI route object

        Returns:
            A unique identifier string
        """
        # Import here to avoid circular dependency
        from fastapi_voyager.type_helper import full_class_name
        return full_class_name(route.endpoint)
