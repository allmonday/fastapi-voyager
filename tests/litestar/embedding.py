"""
Litestar embedding example for fastapi-voyager.

This module demonstrates how to integrate voyager with a Litestar application.
"""
from litestar import Litestar, MediaType, Router, get
from litestar.response import Response

from fastapi_voyager import create_voyager
from tests.litestar.demo import DemoController, diagram

# Create a basic Litestar app with the demo controller
app = Litestar(route_handlers=[DemoController])

# Create voyager app for visualization
# Note: create_voyager automatically detects Litestar and returns a Litestar app
voyager_app = create_voyager(
    app,
    er_diagram=diagram,
    module_color={"tests.service": "purple"},
    module_prefix="tests.service",
    swagger_url="/schema/swagger",
    initial_page_policy='first',
    ga_id='G-R64S7Q49VL',
    online_repo_url="https://github.com/allmonday/fastapi-voyager/blob/main",
    enable_pydantic_resolve_meta=True
)


# Create a wrapper app that includes both the main app and voyager
# Since Litestar doesn't have a built-in mount like FastAPI,
# we create a custom router to handle voyager paths

@get("/voyager/{path:path}", include_in_schema=False)
async def voyager_proxy(path: str) -> Response:
    """
    Proxy voyager requests to the voyager app.

    This is a simple implementation that forwards all requests.
    For production, you might want to use a more sophisticated routing solution.
    """
    # Create a minimal scope for the voyager app
    # Note: This is a simplified version - for production use, you'd want to
    # properly handle the ASGI scope and forwarding
    return Response(
        content="To use voyager with Litestar, access the voyager app directly or implement proper ASGI forwarding",
        status_code=200,
        media_type=MediaType.TEXT,
    )


# For testing purposes, you can run the voyager app directly:
# uvicorn tests.litestar.embedding:voyager_app --reload
#
# For a complete integration, you would need to implement proper ASGI middleware
# or use Litestar's middleware system to forward requests to the voyager app


# Alternative: Direct ASGI integration
# ===================================
# If you want to run both apps together, you can create an ASGI middleware:

async def asgi_app(scope, receive, send):
    """
    ASGI app that routes between main app and voyager.

    Usage:
        uvicorn tests.litestar.embedding:asgi_app --reload
    """
    if scope["type"] == "http" and scope["path"].startswith("/voyager"):
        # Forward to voyager app
        # Remove /voyager prefix for the voyager app
        new_scope = dict(scope)
        new_scope["path"] = scope["path"][8:]  # Remove '/voyager'
        if new_scope["path"] == "":
            new_scope["path"] = "/"
        if "raw_path" in new_scope:
            new_scope["raw_path"] = scope["raw_path"][8:]
        await voyager_app(new_scope, receive, send)
    else:
        # Forward to main app
        await app(scope, receive, send)


# Export for uvicorn
# Use either:
# - uvicorn tests.litestar.embedding:app --reload (main app only)
# - uvicorn tests.litestar.embedding:voyager_app --reload (voyager only)
# - uvicorn tests.litestar.embedding:asgi_app --reload (combined)
