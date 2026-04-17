"""
FastAPI adapter for fastapi-voyager.

This module provides the FastAPI-specific implementation of the voyager server.
"""
from typing import Any, Literal

from pydantic import BaseModel

from fastapi_voyager.adapters.base import VoyagerAdapter
from fastapi_voyager.adapters.common import STATIC_FILES_PATH, VOYAGER_PATH_PLACEHOLDER, VoyagerContext
from fastapi_voyager.type import CoreData, SchemaNode, Tag


class OptionParam(BaseModel):
    tags: list[Tag]
    schemas: list[SchemaNode]
    dot: str
    enable_brief_mode: bool
    version: str
    initial_page_policy: Literal["first", "full", "empty"]
    swagger_url: str | None = None
    has_er_diagram: bool = False
    enable_pydantic_resolve_meta: bool = False
    framework_name: str = "API"


class Payload(BaseModel):
    tags: list[str] | None = None
    schema_name: str | None = None
    schema_field: str | None = None
    route_name: str | None = None
    show_fields: str = "object"
    brief: bool = False
    hide_primitive_route: bool = False
    show_module: bool = True
    show_pydantic_resolve_meta: bool = False


class SearchResultOptionParam(BaseModel):
    tags: list[Tag]


class SchemaSearchPayload(BaseModel):
    schema_name: str | None = None
    schema_field: str | None = None
    show_fields: str = "object"
    brief: bool = False
    hide_primitive_route: bool = False
    show_module: bool = True
    show_pydantic_resolve_meta: bool = False


class ErDiagramPayload(BaseModel):
    show_fields: str = "object"
    show_module: bool = True
    edge_minlen: int = 3
    show_methods: bool = True


class SourcePayload(BaseModel):
    schema_name: str


class FastAPIAdapter(VoyagerAdapter):
    """
    FastAPI-specific implementation of VoyagerAdapter.

    Creates a FastAPI application with voyager endpoints.
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
        server_mode: bool = False,
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
            framework_name="FastAPI",
        )
        self.gzip_minimum_size = gzip_minimum_size
        # Note: server_mode is accepted for API consistency but not used
        # since FastAPI apps are always standalone with routes at /

    def create_app(self) -> Any:
        """Create and return a FastAPI application with voyager endpoints."""
        # Lazy import FastAPI to avoid import errors when framework is not installed
        from fastapi import APIRouter, FastAPI
        from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
        from fastapi.staticfiles import StaticFiles
        from starlette.middleware.gzip import GZipMiddleware

        router = APIRouter(tags=["fastapi-voyager"])

        @router.post("/er-diagram")
        def get_er_diagram(payload: ErDiagramPayload):
            return self.ctx.get_er_diagram_data(payload.model_dump())

        @router.get("/dot", response_model=OptionParam)
        def get_dot() -> OptionParam:
            data = self.ctx.get_option_param()
            return OptionParam(**data)

        @router.post("/dot-search", response_model=SearchResultOptionParam)
        def get_search_dot(payload: SchemaSearchPayload) -> SearchResultOptionParam:
            tags = self.ctx.get_search_dot(payload.model_dump())
            return SearchResultOptionParam(tags=tags)

        @router.post("/dot", response_class=PlainTextResponse)
        def get_filtered_dot(payload: Payload) -> str:
            return self.ctx.get_filtered_dot(payload.model_dump())

        @router.post("/dot-core-data", response_model=CoreData)
        def get_filtered_dot_core_data(payload: Payload) -> CoreData:
            return self.ctx.get_core_data(payload.model_dump())

        @router.post("/dot-render-core-data", response_class=PlainTextResponse)
        def render_dot_from_core_data(core_data: CoreData) -> str:
            return self.ctx.render_dot_from_core_data(core_data)

        @router.get("/", response_class=HTMLResponse)
        def index() -> str:
            return self.ctx.get_index_html()

        @router.get("/sw.js")
        def get_service_worker():
            """Serve the Service Worker with correct content type."""
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(
                content=self.ctx.get_service_worker(),
                media_type="application/javascript"
            )

        @router.get("/manifest.webmanifest")
        def get_manifest():
            """Serve the PWA manifest with correct content type."""
            from fastapi.responses import PlainTextResponse
            content = self.ctx.get_manifest()
            # Replace VOYAGER_PATH with root-relative path (works for any mount point)
            content = content.replace(VOYAGER_PATH_PLACEHOLDER, "./")
            return PlainTextResponse(
                content=content,
                media_type="application/manifest+json"
            )

        @router.post("/source")
        def get_object_by_module_name(payload: SourcePayload) -> JSONResponse:
            result = self.ctx.get_source_code(payload.schema_name)
            status_code = 200 if "error" not in result else 400
            if "error" in result and "not found" in result["error"]:
                status_code = 404
            return JSONResponse(content=result, status_code=status_code)

        @router.post("/vscode-link")
        def get_vscode_link_by_module_name(payload: SourcePayload) -> JSONResponse:
            result = self.ctx.get_vscode_link(payload.schema_name)
            status_code = 200 if "error" not in result else 400
            if "error" in result and "not found" in result["error"]:
                status_code = 404
            return JSONResponse(content=result, status_code=status_code)

        app = FastAPI(title="fastapi-voyager demo server")

        if self.gzip_minimum_size is not None and self.gzip_minimum_size >= 0:
            app.add_middleware(GZipMiddleware, minimum_size=self.gzip_minimum_size)

        from fastapi_voyager.adapters.common import WEB_DIR

        app.mount(STATIC_FILES_PATH, StaticFiles(directory=str(WEB_DIR)), name="static")
        app.include_router(router)

        return app
