"""
Shared business logic for voyager endpoints.

This module contains the core logic that is reused across all framework adapters.
"""
from pathlib import Path
from typing import Any

from pydantic_resolve import ErDiagram

from fastapi_voyager.er_diagram import VoyagerErDiagram
from fastapi_voyager.render import Renderer
from fastapi_voyager.type import CoreData, SchemaNode, Tag
from fastapi_voyager.type_helper import get_source, get_vscode_link
from fastapi_voyager.version import __version__
from fastapi_voyager.voyager import Voyager

WEB_DIR = Path(__file__).parent.parent / "web"
WEB_DIR.mkdir(exist_ok=True)

GA_PLACEHOLDER = "<!-- GA_SNIPPET -->"
VERSION_PLACEHOLDER = "<!-- VERSION_PLACEHOLDER -->"


def build_ga_snippet(ga_id: str | None) -> str:
    """Build Google Analytics snippet."""
    if not ga_id:
        return ""

    return f"""    <script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());

      gtag('config', '{ga_id}');
    </script>
"""


class VoyagerContext:
    """
    Context object that holds configuration and provides business logic methods.

    This is shared across all framework adapters to avoid code duplication.
    """

    def __init__(
        self,
        target_app: Any,
        module_color: dict[str, str] | None = None,
        module_prefix: str | None = None,
        swagger_url: str | None = None,
        online_repo_url: str | None = None,
        initial_page_policy: str = 'first',
        ga_id: str | None = None,
        er_diagram: ErDiagram | None = None,
        enable_pydantic_resolve_meta: bool = False,
        framework_name: str | None = None,
    ):
        self.target_app = target_app
        self.module_color = module_color or {}
        self.module_prefix = module_prefix
        self.swagger_url = swagger_url
        self.online_repo_url = online_repo_url
        self.initial_page_policy = initial_page_policy
        self.ga_id = ga_id
        self.er_diagram = er_diagram
        self.enable_pydantic_resolve_meta = enable_pydantic_resolve_meta
        self.framework_name = framework_name or "API"

    def get_voyager(self, **kwargs) -> Voyager:
        """Create a Voyager instance with common configuration."""
        config = {
            "module_color": self.module_color,
            "show_pydantic_resolve_meta": self.enable_pydantic_resolve_meta,
        }
        config.update(kwargs)
        return Voyager(**config)

    def analyze_and_get_dot(self) -> tuple[str, list[Tag], list[SchemaNode]]:
        """
        Analyze the target app and return dot graph, tags, and schemas.

        Returns:
            Tuple of (dot_graph, tags, schemas)
        """
        voyager = self.get_voyager()
        voyager.analysis(self.target_app)
        dot = voyager.render_dot()

        # include tags and their routes
        tags = voyager.tags
        for t in tags:
            t.routes.sort(key=lambda r: r.name)
        tags.sort(key=lambda t: t.name)

        schemas = voyager.nodes[:]
        schemas.sort(key=lambda s: s.name)

        return dot, tags, schemas

    def get_option_param(self) -> dict:
        """Get the option parameter for the voyager UI."""
        dot, tags, schemas = self.analyze_and_get_dot()

        return {
            "tags": tags,
            "schemas": schemas,
            "dot": dot,
            "enable_brief_mode": bool(self.module_prefix),
            "version": __version__,
            "swagger_url": self.swagger_url,
            "initial_page_policy": self.initial_page_policy,
            "has_er_diagram": self.er_diagram is not None,
            "enable_pydantic_resolve_meta": self.enable_pydantic_resolve_meta,
            "framework_name": self.framework_name,
        }

    def get_search_dot(self, payload: dict) -> list[Tag]:
        """Get filtered tags for search."""
        voyager = self.get_voyager(
            schema=payload.get("schema_name"),
            schema_field=payload.get("schema_field"),
            show_fields=payload.get("show_fields", "object"),
            hide_primitive_route=payload.get("hide_primitive_route", False),
            show_module=payload.get("show_module", True),
            show_pydantic_resolve_meta=payload.get("show_pydantic_resolve_meta", False),
        )
        voyager.analysis(self.target_app)
        tags = voyager.calculate_filtered_tag_and_route()

        for t in tags:
            t.routes.sort(key=lambda r: r.name)
        tags.sort(key=lambda t: t.name)

        return tags

    def get_filtered_dot(self, payload: dict) -> str:
        """Get filtered dot graph."""
        voyager = self.get_voyager(
            include_tags=payload.get("tags"),
            schema=payload.get("schema_name"),
            schema_field=payload.get("schema_field"),
            show_fields=payload.get("show_fields", "object"),
            route_name=payload.get("route_name"),
            hide_primitive_route=payload.get("hide_primitive_route", False),
            show_module=payload.get("show_module", True),
            show_pydantic_resolve_meta=payload.get("show_pydantic_resolve_meta", False),
        )
        voyager.analysis(self.target_app)

        if payload.get("brief"):
            if payload.get("tags"):
                return voyager.render_tag_level_brief_dot(module_prefix=self.module_prefix)
            else:
                return voyager.render_overall_brief_dot(module_prefix=self.module_prefix)
        else:
            return voyager.render_dot()

    def get_core_data(self, payload: dict) -> CoreData:
        """Get core data for the graph."""
        voyager = self.get_voyager(
            include_tags=payload.get("tags"),
            schema=payload.get("schema_name"),
            schema_field=payload.get("schema_field"),
            show_fields=payload.get("show_fields", "object"),
            route_name=payload.get("route_name"),
        )
        voyager.analysis(self.target_app)
        return voyager.dump_core_data()

    def render_dot_from_core_data(self, core_data: CoreData) -> str:
        """Render dot graph from core data."""
        renderer = Renderer(
            show_fields=core_data.show_fields,
            module_color=core_data.module_color,
            schema=core_data.schema,
        )
        return renderer.render_dot(
            core_data.tags, core_data.routes, core_data.nodes, core_data.links
        )

    def get_er_diagram_dot(self, payload: dict) -> str:
        """Get ER diagram dot graph."""
        if self.er_diagram:
            return VoyagerErDiagram(
                self.er_diagram,
                show_fields=payload.get("show_fields", "object"),
                show_module=payload.get("show_module", True),
            ).render_dot()
        return ""

    def get_index_html(self) -> str:
        """Get the index HTML content."""
        index_file = WEB_DIR / "index.html"
        if index_file.exists():
            content = index_file.read_text(encoding="utf-8")
            content = content.replace(GA_PLACEHOLDER, build_ga_snippet(self.ga_id))
            content = content.replace(VERSION_PLACEHOLDER, f"?v={__version__}")
            return content
        # fallback simple page if index.html missing
        return """
        <!doctype html>
        <html>
        <head><meta charset="utf-8"><title>Graphviz Preview</title></head>
        <body>
          <p>index.html not found. Create one under src/fastapi_voyager/web/index.html</p>
        </body>
        </html>
        """

    def get_source_code(self, schema_name: str) -> dict:
        """Get source code for a schema."""
        try:
            components = schema_name.split(".")
            if len(components) < 2:
                return {"error": "Invalid schema name format. Expected format: module.ClassName"}

            module_name = ".".join(components[:-1])
            class_name = components[-1]

            mod = __import__(module_name, fromlist=[class_name])
            obj = getattr(mod, class_name)
            source_code = get_source(obj)

            return {"source_code": source_code}
        except ImportError as e:
            return {"error": f"Module not found: {e}"}
        except AttributeError as e:
            return {"error": f"Class not found: {e}"}
        except Exception as e:
            return {"error": f"Internal error: {str(e)}"}

    def get_vscode_link(self, schema_name: str) -> dict:
        """Get VSCode link for a schema."""
        try:
            components = schema_name.split(".")
            if len(components) < 2:
                return {"error": "Invalid schema name format. Expected format: module.ClassName"}

            module_name = ".".join(components[:-1])
            class_name = components[-1]

            mod = __import__(module_name, fromlist=[class_name])
            obj = getattr(mod, class_name)
            link = get_vscode_link(obj, online_repo_url=self.online_repo_url)

            return {"link": link}
        except ImportError as e:
            return {"error": f"Module not found: {e}"}
        except AttributeError as e:
            return {"error": f"Class not found: {e}"}
        except Exception as e:
            return {"error": f"Internal error: {str(e)}"}
