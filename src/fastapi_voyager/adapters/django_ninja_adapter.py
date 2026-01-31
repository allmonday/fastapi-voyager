"""
Django Ninja adapter for fastapi-voyager.

This module provides the Django Ninja-specific implementation of the voyager server.
It creates an ASGI application that can be integrated with Django.
"""
import json
import mimetypes
from typing import Any

from fastapi_voyager.adapters.base import VoyagerAdapter
from fastapi_voyager.adapters.common import WEB_DIR, VoyagerContext
from fastapi_voyager.type import CoreData, SchemaNode, Tag


class DjangoNinjaAdapter(VoyagerAdapter):
    """
    Django Ninja-specific implementation of VoyagerAdapter.

    Creates an ASGI application with voyager endpoints that can be integrated with Django.
    """

    def __init__(
        self,
        target_app: Any,
        module_color: dict[str, str] | None = None,
        gzip_minimum_size: int | None = 500,
        module_prefix: str | None = None,
        swagger_url: str | None = None,
        online_repo_url: str | None = None,
        initial_page_policy: str = "first",
        ga_id: str | None = None,
        er_diagram: Any = None,
        enable_pydantic_resolve_meta: bool = False,
    ):
        self.ctx = VoyagerContext(
            target_app=target_app,
            module_color=module_color,
            module_prefix=module_prefix,
            swagger_url=swagger_url,
            online_repo_url=online_repo_url,
            initial_page_policy=initial_page_policy,
            ga_id=ga_id,
            er_diagram=er_diagram,
            enable_pydantic_resolve_meta=enable_pydantic_resolve_meta,
            framework_name="Django Ninja",
        )
        # Note: gzip should be handled by Django's middleware, not here

    async def _handle_request(self, scope, receive, send):
        """ASGI request handler."""
        if scope["type"] != "http":
            return

        # Parse the request
        method = scope["method"]
        path = scope["path"]
        # Remove /voyager prefix for internal routing
        if path.startswith("/voyager"):
            path = path[8:]  # Remove '/voyager'
            if path == "":
                path = "/"

        # Handle static files
        if method == "GET" and path.startswith("/fastapi-voyager-static/"):
            await self._handle_static_file(path, send)
            return

        # Route the request
        if method == "GET" and path == "/":
            await self._handle_index(send)
        elif method == "GET" and path == "/dot":
            await self._handle_get_dot(send)
        elif method == "POST" and path == "/er-diagram":
            await self._handle_post_request(receive, send, self._handle_er_diagram)
        elif method == "POST" and path == "/dot-search":
            await self._handle_post_request(receive, send, self._handle_search_dot)
        elif method == "POST" and path == "/dot":
            await self._handle_post_request(receive, send, self._handle_filtered_dot)
        elif method == "POST" and path == "/dot-core-data":
            await self._handle_post_request(receive, send, self._handle_core_data)
        elif method == "POST" and path == "/dot-render-core-data":
            await self._handle_post_request(receive, send, self._handle_render_core_data)
        elif method == "POST" and path == "/source":
            await self._handle_post_request(receive, send, self._handle_source)
        elif method == "POST" and path == "/vscode-link":
            await self._handle_post_request(receive, send, self._handle_vscode_link)
        else:
            await self._send_404(send)

    async def _handle_post_request(self, receive, send, handler):
        """Helper to handle POST requests with JSON body."""
        body = b""
        more_body = True

        while more_body:
            message = await receive()
            if message["type"] == "http.request":
                body += message.get("body", b"")
                more_body = message.get("more_body", False)

        try:
            payload = json.loads(body.decode())
            await handler(payload, send)
        except Exception as e:
            await self._send_json({"error": str(e)}, send, status_code=400)

    async def _handle_static_file(self, path: str, send):
        """Handle GET /fastapi-voyager-static/* - serve static files."""
        # Remove /fastapi-voyager-static/ prefix
        file_path = path[len("/fastapi-voyager-static/"):]
        full_path = WEB_DIR / file_path

        # Security check: ensure the path is within WEB_DIR
        try:
            full_path = full_path.resolve()
            web_dir_resolved = WEB_DIR.resolve()
            if not str(full_path).startswith(str(web_dir_resolved)):
                await self._send_404(send)
                return
        except Exception:
            await self._send_404(send)
            return

        if not full_path.exists() or not full_path.is_file():
            await self._send_404(send)
            return

        # Read file content
        try:
            with open(full_path, "rb") as f:
                content = f.read()

            # Determine content type
            content_type, _ = mimetypes.guess_type(str(full_path))
            if content_type is None:
                content_type = "application/octet-stream"

            await self._send_response(content_type, content, send)
        except Exception:
            await self._send_404(send)

    async def _handle_index(self, send):
        """Handle GET / - return the index HTML."""
        html = self.ctx.get_index_html()
        await self._send_html(html, send)

    async def _handle_get_dot(self, send):
        """Handle GET /dot - return options and initial dot graph."""
        data = self.ctx.get_option_param()
        # Convert tags and schemas to dicts for JSON serialization
        response_data = {
            "tags": [self._tag_to_dict(t) for t in data["tags"]],
            "schemas": [self._schema_to_dict(s) for s in data["schemas"]],
            "dot": data["dot"],
            "enable_brief_mode": data["enable_brief_mode"],
            "version": data["version"],
            "initial_page_policy": data["initial_page_policy"],
            "swagger_url": data["swagger_url"],
            "has_er_diagram": data["has_er_diagram"],
            "enable_pydantic_resolve_meta": data["enable_pydantic_resolve_meta"],
            "framework_name": data["framework_name"],
        }
        await self._send_json(response_data, send)

    async def _handle_er_diagram(self, payload, send):
        """Handle POST /er-diagram."""
        dot = self.ctx.get_er_diagram_dot(payload)
        await self._send_text(dot, send)

    async def _handle_search_dot(self, payload, send):
        """Handle POST /dot-search."""
        tags = self.ctx.get_search_dot(payload)
        response_data = {"tags": [self._tag_to_dict(t) for t in tags]}
        await self._send_json(response_data, send)

    async def _handle_filtered_dot(self, payload, send):
        """Handle POST /dot."""
        dot = self.ctx.get_filtered_dot(payload)
        await self._send_text(dot, send)

    async def _handle_core_data(self, payload, send):
        """Handle POST /dot-core-data."""
        core_data = self.ctx.get_core_data(payload)
        await self._send_json(core_data.model_dump(), send)

    async def _handle_render_core_data(self, payload, send):
        """Handle POST /dot-render-core-data."""
        core_data = CoreData(**payload)
        dot = self.ctx.render_dot_from_core_data(core_data)
        await self._send_text(dot, send)

    async def _handle_source(self, payload, send):
        """Handle POST /source."""
        result = self.ctx.get_source_code(payload.get("schema_name", ""))
        status_code = 200 if "error" not in result else 400
        if "error" in result and "not found" in result["error"]:
            status_code = 404
        await self._send_json(result, send, status_code=status_code)

    async def _handle_vscode_link(self, payload, send):
        """Handle POST /vscode-link."""
        result = self.ctx.get_vscode_link(payload.get("schema_name", ""))
        status_code = 200 if "error" not in result else 400
        if "error" in result and "not found" in result["error"]:
            status_code = 404
        await self._send_json(result, send, status_code=status_code)

    async def _send_html(self, html: str, send):
        """Send HTML response."""
        await self._send_response(
            "text/html; charset=utf-8",
            html.encode("utf-8"),
            send,
            status_code=200,
        )

    async def _send_json(self, data: dict, send, status_code: int = 200):
        """Send JSON response."""
        body = json.dumps(data).encode("utf-8")
        await self._send_response("application/json", body, send, status_code=status_code)

    async def _send_text(self, text: str, send):
        """Send plain text response."""
        await self._send_response("text/plain; charset=utf-8", text.encode("utf-8"), send)

    async def _send_404(self, send):
        """Send 404 response."""
        await self._send_response("text/plain", b"Not Found", send, status_code=404)

    async def _send_response(
        self, content_type: str, body: bytes, send, status_code: int = 200
    ):
        """Send ASGI response."""
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    [b"content-type", content_type.encode()],
                    [b"content-length", str(len(body)).encode()],
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    def _tag_to_dict(self, tag: Tag) -> dict:
        """Convert Tag object to dict."""
        return {
            "id": tag.id,
            "name": tag.name,
            "routes": [
                {
                    "id": r.id,
                    "name": r.name,
                    "module": r.module,
                    "unique_id": r.unique_id,
                    "response_schema": r.response_schema,
                    "is_primitive": r.is_primitive,
                }
                for r in tag.routes
            ],
        }

    def _schema_to_dict(self, schema: SchemaNode) -> dict:
        """Convert SchemaNode to dict."""
        return {
            "id": schema.id,
            "module": schema.module,
            "name": schema.name,
            "fields": [
                {
                    "name": f.name,
                    "type_name": f.type_name,
                    "is_object": f.is_object,
                    "is_exclude": f.is_exclude,
                }
                for f in schema.fields
            ],
        }

    def create_app(self):
        """Create and return an ASGI application."""

        async def asgi_app(scope, receive, send):
            # Route /voyager/* to voyager handler
            if scope["type"] == "http" and scope["path"].startswith("/voyager"):
                await self._handle_request(scope, receive, send)
            else:
                # Return 404 for non-voyager paths
                # (Django should handle these before they reach here)
                await self._send_404(send)

        return asgi_app

    def get_mount_path(self) -> str:
        """Get the recommended mount path for voyager."""
        return "/voyager"
