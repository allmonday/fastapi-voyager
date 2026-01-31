"""
Litestar adapter for fastapi-voyager.

This module provides the Litestar-specific implementation of the voyager server.
"""
from typing import Any

from litestar import Litestar, MediaType, Request, Response, get, post
from litestar.static_files import StaticFilesConfig

from fastapi_voyager.adapters.base import VoyagerAdapter
from fastapi_voyager.adapters.common import WEB_DIR, VoyagerContext
from fastapi_voyager.type import CoreData, SchemaNode, Tag


class LitestarAdapter(VoyagerAdapter):
    """
    Litestar-specific implementation of VoyagerAdapter.

    Creates a Litestar application with voyager endpoints.
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
            framework_name="Litestar",
        )
        self.gzip_minimum_size = gzip_minimum_size

    def create_app(self) -> Litestar:
        """Create and return a Litestar application with voyager endpoints."""

        @get("/er-diagram")
        async def get_er_diagram(request: Request) -> str:
            payload = await request.json()
            return self.ctx.get_er_diagram_dot(payload)

        @get("/dot")
        async def get_dot(request: Request) -> dict:
            data = self.ctx.get_option_param()
            # Convert tags and schemas to dicts for JSON serialization
            return {
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

        @post("/dot-search")
        async def get_search_dot(request: Request) -> dict:
            payload = await request.json()
            tags = self.ctx.get_search_dot(payload)
            return {"tags": [self._tag_to_dict(t) for t in tags]}

        @post("/dot")
        async def get_filtered_dot(request: Request) -> str:
            payload = await request.json()
            return self.ctx.get_filtered_dot(payload)

        @post("/dot-core-data")
        async def get_filtered_dot_core_data(request: Request) -> CoreData:
            payload = await request.json()
            return self.ctx.get_core_data(payload)

        @post("/dot-render-core-data")
        async def render_dot_from_core_data(request: Request) -> str:
            payload = await request.json()
            core_data = CoreData(**payload)
            return self.ctx.render_dot_from_core_data(core_data)

        @get("/", media_type=MediaType.HTML)
        async def index() -> str:
            return self.ctx.get_index_html()

        @post("/source")
        async def get_object_by_module_name(request: Request) -> dict:
            payload = await request.json()
            result = self.ctx.get_source_code(payload.get("schema_name", ""))
            status_code = 200 if "error" not in result else 400
            if "error" in result and "not found" in result["error"]:
                status_code = 404
            return Response(
                content=result,
                status_code=status_code,
                media_type=MediaType.JSON,
            )

        @post("/vscode-link")
        async def get_vscode_link_by_module_name(request: Request) -> dict:
            payload = await request.json()
            result = self.ctx.get_vscode_link(payload.get("schema_name", ""))
            status_code = 200 if "error" not in result else 400
            if "error" in result and "not found" in result["error"]:
                status_code = 404
            return Response(
                content=result,
                status_code=status_code,
                media_type=MediaType.JSON,
            )

        # Create Litestar app
        app = Litestar(
            route_handlers=[
                get_er_diagram,
                get_dot,
                get_search_dot,
                get_filtered_dot,
                get_filtered_dot_core_data,
                render_dot_from_core_data,
                index,
                get_object_by_module_name,
                get_vscode_link_by_module_name,
            ],
            static_files_config=[
                StaticFilesConfig(path="/fastapi-voyager-static", directories=[str(WEB_DIR)])
            ],
        )

        return app

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

    def get_mount_path(self) -> str:
        """Get the recommended mount path for voyager."""
        return "/voyager"
