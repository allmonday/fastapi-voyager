"""
Introspection abstraction layer for framework-agnostic route analysis.

This module provides the abstraction that allows fastapi-voyager to work with
different web frameworks that support OpenAPI and Pydantic, such as:
- FastAPI
- Django Ninja
- Litestar
- Flask-OpenAPI
"""
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any


@dataclass
class RouteInfo:
    """
    Standardized route information that works across different frameworks.

    This data class encapsulates the essential information needed by voyager
    to analyze and visualize routes, independent of the underlying framework.
    """
    # Unique identifier for the route (function path)
    id: str

    # Human-readable name (function name)
    name: str

    # Module where the route handler is defined
    module: str

    # Operation ID from OpenAPI spec
    operation_id: str | None

    # List of tags associated with this route
    tags: list[str]

    # The route handler function/endpoint
    endpoint: Callable

    # Response model (should be a Pydantic BaseModel)
    response_model: type[Any]

    # Any additional framework-specific data
    extra: dict[str, Any] | None = None


class AppIntrospector(ABC):
    """
    Abstract base class for app introspection.

    Implement this class to add support for different web frameworks.
    The introspector is responsible for extracting route information
    from the framework's internal structure.
    """

    @abstractmethod
    def get_routes(self) -> Iterator[RouteInfo]:
        """
        Iterate over all available routes in the application.

        Yields:
            RouteInfo: Standardized route information

        Example:
            >>> for route in introspector.get_routes():
            ...     print(f"{route.id}: {route.tags}")
        """
        pass

    @abstractmethod
    def get_swagger_url(self) -> str | None:
        """
        Get the URL to the Swagger/OpenAPI documentation.

        Returns:
            The URL path or None if not available
        """
        pass
