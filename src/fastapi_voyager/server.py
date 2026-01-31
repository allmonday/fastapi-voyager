"""
FastAPI-voyager server module with framework adapter support.

This module provides the main `create_voyager` function that automatically
detects the framework type and returns an appropriately configured voyager UI.
"""
from typing import Any, Literal

from pydantic_resolve import ErDiagram

from fastapi_voyager.adapters import DjangoNinjaAdapter, FastAPIAdapter, LitestarAdapter

INITIAL_PAGE_POLICY = Literal["first", "full", "empty"]


def _get_adapter(
    target_app: Any,
    module_color: dict[str, str] | None = None,
    gzip_minimum_size: int | None = 500,
    module_prefix: str | None = None,
    swagger_url: str | None = None,
    online_repo_url: str | None = None,
    initial_page_policy: INITIAL_PAGE_POLICY = "first",
    ga_id: str | None = None,
    er_diagram: ErDiagram | None = None,
    enable_pydantic_resolve_meta: bool = False,
) -> Any:
    """
    Get the appropriate adapter for the given target app.

    Automatically detects the framework type and returns the matching adapter.

    Args:
        target_app: The web application instance to introspect
        module_color: Optional color mapping for modules
        gzip_minimum_size: Minimum size for gzip compression
        module_prefix: Optional module prefix for filtering
        swagger_url: Optional custom URL to Swagger documentation
        online_repo_url: Optional online repository URL for source links
        initial_page_policy: Initial page display policy
        ga_id: Optional Google Analytics ID
        er_diagram: Optional ER diagram from pydantic-resolve
        enable_pydantic_resolve_meta: Enable pydantic-resolve metadata display

    Returns:
        An adapter instance for the detected framework

    Raises:
        TypeError: If the app type is not supported
    """
    # Try FastAPI
    try:
        from fastapi import FastAPI

        if isinstance(target_app, FastAPI):
            return FastAPIAdapter(
                target_app=target_app,
                module_color=module_color,
                gzip_minimum_size=gzip_minimum_size,
                module_prefix=module_prefix,
                swagger_url=swagger_url,
                online_repo_url=online_repo_url,
                initial_page_policy=initial_page_policy,
                ga_id=ga_id,
                er_diagram=er_diagram,
                enable_pydantic_resolve_meta=enable_pydantic_resolve_meta,
            )
    except ImportError:
        pass

    # Try Django Ninja
    try:
        from ninja import NinjaAPI

        if isinstance(target_app, NinjaAPI):
            return DjangoNinjaAdapter(
                target_app=target_app,
                module_color=module_color,
                gzip_minimum_size=gzip_minimum_size,  # Note: ignored for Django
                module_prefix=module_prefix,
                swagger_url=swagger_url,
                online_repo_url=online_repo_url,
                initial_page_policy=initial_page_policy,
                ga_id=ga_id,
                er_diagram=er_diagram,
                enable_pydantic_resolve_meta=enable_pydantic_resolve_meta,
            )
    except ImportError:
        pass

    # Try Litestar
    try:
        from litestar import Litestar

        if isinstance(target_app, Litestar):
            return LitestarAdapter(
                target_app=target_app,
                module_color=module_color,
                gzip_minimum_size=gzip_minimum_size,
                module_prefix=module_prefix,
                swagger_url=swagger_url,
                online_repo_url=online_repo_url,
                initial_page_policy=initial_page_policy,
                ga_id=ga_id,
                er_diagram=er_diagram,
                enable_pydantic_resolve_meta=enable_pydantic_resolve_meta,
            )
    except ImportError:
        pass

    # If we get here, the app type is not supported
    raise TypeError(
        f"Unsupported app type: {type(target_app).__name__}. "
        f"Supported types: FastAPI, Django Ninja API, Litestar. "
        f"If you're using a different framework, please implement a VoyagerAdapter for that framework. "
        f"See fastapi_voyager/adapters/ for examples."
    )


def create_voyager(
    target_app: Any,
    module_color: dict[str, str] | None = None,
    gzip_minimum_size: int | None = 500,
    module_prefix: str | None = None,
    swagger_url: str | None = None,
    online_repo_url: str | None = None,
    initial_page_policy: INITIAL_PAGE_POLICY = "first",
    ga_id: str | None = None,
    er_diagram: ErDiagram | None = None,
    enable_pydantic_resolve_meta: bool = False,
) -> Any:
    """
    Create a voyager UI application for the given target app.

    This function automatically detects the framework type (FastAPI, Django Ninja, or Litestar)
    and returns an appropriately configured voyager UI application.

    For FastAPI: Returns a FastAPI app that can be mounted
    For Django Ninja: Returns an ASGI application
    For Litestar: Returns a Litestar app

    Args:
        target_app: The web application to visualize
        module_color: Optional color mapping for modules (e.g., {"myapp": "blue"})
        gzip_minimum_size: Minimum response size for gzip compression (set to <0 to disable)
        module_prefix: Optional module prefix for filtering/organization
        swagger_url: Optional custom URL to Swagger/OpenAPI documentation
        online_repo_url: Optional base URL for online repository source links
        initial_page_policy: Initial page display policy ('first', 'full', or 'empty')
        ga_id: Optional Google Analytics tracking ID
        er_diagram: Optional ER diagram from pydantic-resolve
        enable_pydantic_resolve_meta: Enable display of pydantic-resolve metadata

    Returns:
        A framework-specific application object that provides the voyager UI

    Example:
        # FastAPI
        from fastapi import FastAPI
        from fastapi_voyager import create_voyager

        app = FastAPI()
        voyager_app = create_voyager(app)
        app.mount("/voyager", voyager_app)

        # Django Ninja
        from ninja import NinjaAPI
        from fastapi_voyager import create_voyager

        api = NinjaAPI()
        voyager_asgi_app = create_voyager(api)
        # See django_ninja tests for integration examples

        # Litestar
        from litestar import Litestar
        from fastapi_voyager import create_voyager

        app = Litestar()
        voyager_app = create_voyager(app)
        # Mount or integrate as needed
    """
    adapter = _get_adapter(
        target_app=target_app,
        module_color=module_color,
        gzip_minimum_size=gzip_minimum_size,
        module_prefix=module_prefix,
        swagger_url=swagger_url,
        online_repo_url=online_repo_url,
        initial_page_policy=initial_page_policy,
        ga_id=ga_id,
        er_diagram=er_diagram,
        enable_pydantic_resolve_meta=enable_pydantic_resolve_meta,
    )

    return adapter.create_app()
