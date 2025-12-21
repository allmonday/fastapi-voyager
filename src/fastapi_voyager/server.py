from pathlib import Path
from typing import Literal

from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.gzip import GZipMiddleware

from fastapi_voyager.render import Renderer
from fastapi_voyager.type import CoreData, SchemaNode, Tag
from fastapi_voyager.type_helper import get_source, get_vscode_link
from fastapi_voyager.version import __version__
from fastapi_voyager.voyager import Voyager
from pydantic_resolve import ErDiagram
from fastapi_voyager.er_diagram import VoyagerErDiagram

WEB_DIR = Path(__file__).parent / "web"
WEB_DIR.mkdir(exist_ok=True)

GA_PLACEHOLDER = "<!-- GA_SNIPPET -->"

def _build_ga_snippet(ga_id: str | None) -> str:
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

INITIAL_PAGE_POLICY = Literal['first', 'full', 'empty']

# ---------- setup ----------

class OptionParam(BaseModel):
	tags: list[Tag]
	schemas: list[SchemaNode]
	dot: str
	enable_brief_mode: bool
	version: str
	initial_page_policy: INITIAL_PAGE_POLICY
	swagger_url: str | None = None
	has_er_diagram: bool = False
	enable_pydantic_resolve_meta: bool = False

class Payload(BaseModel):
	tags: list[str] | None = None
	schema_name: str | None = None
	schema_field: str | None = None
	route_name: str | None = None
	show_fields: str = 'object'
	brief: bool = False
	hide_primitive_route: bool = False
	show_module: bool = True
	show_pydantic_resolve_meta: bool = False

# ---------- search ----------
class SearchResultOptionParam(BaseModel):
	tags: list[Tag]

class SchemaSearchPayload(BaseModel):  # leave tag, route out
	schema_name: str | None = None
	schema_field: str | None = None
	show_fields: str = 'object'
	brief: bool = False
	hide_primitive_route: bool = False
	show_module: bool = True


# ---------- er diagram ----------
class ErDiagramPayload(BaseModel):
	show_fields: str = 'object'
	show_module: bool = True

def create_voyager(
	target_app: FastAPI,
	module_color: dict[str, str] | None = None,
	gzip_minimum_size: int | None = 500,
	module_prefix: str | None = None,
	swagger_url: str | None = None,
	online_repo_url: str | None = None,
	initial_page_policy: INITIAL_PAGE_POLICY = 'first',
	ga_id: str | None = None,
	er_diagram: ErDiagram | None = None,
	enable_pydantic_resolve_meta: bool = False,
) -> FastAPI:
	router = APIRouter(tags=['fastapi-voyager'])

	@router.post("/er-diagram", response_class=PlainTextResponse)
	def get_er_diagram(payload: ErDiagramPayload) -> str:
		if er_diagram:
			return VoyagerErDiagram(
				er_diagram,
				show_fields=payload.show_fields,
				show_module=payload.show_module ).render_dot()
		return ''

	@router.get("/dot", response_model=OptionParam)
	def get_dot() -> str:
		voyager = Voyager(module_color=module_color)
		voyager.analysis(target_app)
		dot = voyager.render_dot()

		# include tags and their routes
		tags = voyager.tags
		for t in tags:
			t.routes.sort(key=lambda r: r.name)
		tags.sort(key=lambda t: t.name)

		schemas = voyager.nodes[:]
		schemas.sort(key=lambda s: s.name)

		return OptionParam(
			tags=tags, 
			schemas=schemas,
			dot=dot,
			enable_brief_mode=bool(module_prefix),
			version=__version__,
			swagger_url=swagger_url,
			initial_page_policy=initial_page_policy,
			has_er_diagram=er_diagram is not None, 
			enable_pydantic_resolve_meta=enable_pydantic_resolve_meta)


	@router.post("/dot-search", response_model=SearchResultOptionParam)
	def get_search_dot(payload: SchemaSearchPayload):
		voyager = Voyager(
			schema=payload.schema_name,
			schema_field=payload.schema_field,
			show_fields=payload.show_fields,
			module_color=module_color,
			hide_primitive_route=payload.hide_primitive_route,
			show_module=payload.show_module,
			show_pydantic_resolve_meta=payload.show_pydantic_resolve_meta,
		)
		voyager.analysis(target_app)
		tags = voyager.calculate_filtered_tag_and_route()

		for t in tags:
			t.routes.sort(key=lambda r: r.name)
		tags.sort(key=lambda t: t.name)

		return SearchResultOptionParam(tags=tags)

	@router.post("/dot", response_class=PlainTextResponse)
	def get_filtered_dot(payload: Payload) -> str:
		voyager = Voyager(
			include_tags=payload.tags,
			schema=payload.schema_name,
			schema_field=payload.schema_field,
			show_fields=payload.show_fields,
			module_color=module_color,
			route_name=payload.route_name,
			hide_primitive_route=payload.hide_primitive_route,
			show_module=payload.show_module,
			show_pydantic_resolve_meta=payload.show_pydantic_resolve_meta,
		)
		voyager.analysis(target_app)
		if payload.brief:
			if payload.tags:
				return voyager.render_tag_level_brief_dot(module_prefix=module_prefix)
			else:
				return voyager.render_overall_brief_dot(module_prefix=module_prefix)
		else:
			return voyager.render_dot()

	@router.post("/dot-core-data", response_model=CoreData)
	def get_filtered_dot_core_data(payload: Payload) -> str:
		voyager = Voyager(
			include_tags=payload.tags,
			schema=payload.schema_name,
			schema_field=payload.schema_field,
			show_fields=payload.show_fields,
			module_color=module_color,
			route_name=payload.route_name,
		)
		voyager.analysis(target_app)
		return voyager.dump_core_data()

	@router.post('/dot-render-core-data', response_class=PlainTextResponse)
	def render_dot_from_core_data(core_data: CoreData) -> str:
		renderer = Renderer(
			show_fields=core_data.show_fields,
			module_color=core_data.module_color,
			schema=core_data.schema)
		return renderer.render_dot(core_data.tags, core_data.routes, core_data.nodes, core_data.links)

	@router.get("/", response_class=HTMLResponse)
	def index():
		index_file = WEB_DIR / "index.html"
		if index_file.exists():
			content = index_file.read_text(encoding="utf-8")
			return content.replace(GA_PLACEHOLDER, _build_ga_snippet(ga_id))
		# fallback simple page if index.html missing
		return """
		<!doctype html>
		<html>
		<head><meta charset=\"utf-8\"><title>Graphviz Preview</title></head>
		<body>
		  <p>index.html not found. Create one under src/fastapi_voyager/web/index.html</p>
		</body>
		</html>
		"""
	
	class SourcePayload(BaseModel):
		schema_name: str

	@router.post("/source")
	def get_object_by_module_name(payload: SourcePayload):
		"""
		input: __module__ + __name__, eg: tests.demo.PageStories
		output: source code of the object
		"""
		try:
			components = payload.schema_name.split('.')
			if len(components) < 2:
				return JSONResponse(
					status_code=400, 
					content={"error": "Invalid schema name format. Expected format: module.ClassName"}
				)
			
			module_name = '.'.join(components[:-1])
			class_name = components[-1]
			
			mod = __import__(module_name, fromlist=[class_name])
			obj = getattr(mod, class_name)
			source_code = get_source(obj)
			
			return JSONResponse(content={"source_code": source_code})
		except ImportError as e:
			return JSONResponse(
				status_code=404,
				content={"error": f"Module not found: {e}"}
			)
		except AttributeError as e:
			return JSONResponse(
				status_code=404,
				content={"error": f"Class not found: {e}"}
			)
		except Exception as e:
			return JSONResponse(
				status_code=500,
				content={"error": f"Internal error: {str(e)}"}
			)

	@router.post("/vscode-link")
	def get_vscode_link_by_module_name(payload: SourcePayload):
		"""
		input: __module__ + __name__, eg: tests.demo.PageStories
		output: source path of the object
		"""
		try:
			components = payload.schema_name.split('.')
			if len(components) < 2:
				return JSONResponse(
					status_code=400, 
					content={"error": "Invalid schema name format. Expected format: module.ClassName"}
				)
			
			module_name = '.'.join(components[:-1])
			class_name = components[-1]
			
			mod = __import__(module_name, fromlist=[class_name])
			obj = getattr(mod, class_name)
			link = get_vscode_link(obj, online_repo_url=online_repo_url)
			
			return JSONResponse(content={"link": link})
		except ImportError as e:
			return JSONResponse(
				status_code=404,
				content={"error": f"Module not found: {e}"}
			)
		except AttributeError as e:
			return JSONResponse(
				status_code=404,
				content={"error": f"Class not found: {e}"}
			)
		except Exception as e:
			return JSONResponse(
				status_code=500,
				content={"error": f"Internal error: {str(e)}"}
			)
        
	app = FastAPI(title="fastapi-voyager demo server")
	if gzip_minimum_size is not None and gzip_minimum_size >= 0:
		app.add_middleware(GZipMiddleware, minimum_size=gzip_minimum_size)

	app.mount("/fastapi-voyager-static", StaticFiles(directory=str(WEB_DIR)), name="static")
	app.include_router(router)

	return app

