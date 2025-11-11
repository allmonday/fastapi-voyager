from pathlib import Path
from typing import Optional, Literal
from fastapi import FastAPI, APIRouter
from starlette.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi_voyager.voyager import Voyager
from fastapi_voyager.type import Tag, FieldInfo, CoreData, SchemaNode
from fastapi_voyager.render import Renderer
from fastapi_voyager.type_helper import get_source, get_vscode_link
from fastapi_voyager.version import __version__


WEB_DIR = Path(__file__).parent / "web"
WEB_DIR.mkdir(exist_ok=True)

INITIAL_PAGE_POLICY = Literal['first', 'full', 'empty']

class OptionParam(BaseModel):
	tags: list[Tag]
	schemas: list[SchemaNode]
	dot: str
	enable_brief_mode: bool
	version: str
	initial_page_policy: INITIAL_PAGE_POLICY
	swagger_url: Optional[str] = None

class Payload(BaseModel):
	tags: Optional[list[str]] = None
	schema_name: Optional[str] = None
	schema_field: Optional[str] = None
	route_name: Optional[str] = None
	show_fields: str = 'object'
	show_meta: bool = False
	brief: bool = False
	hide_primitive_route: bool = False
	show_module: bool = True


def create_voyager(
	target_app: FastAPI,
	module_color: dict[str, str] | None = None,
	gzip_minimum_size: int | None = 500,
	module_prefix: Optional[str] = None,
	swagger_url: Optional[str] = None,
	online_repo_url: Optional[str] = None,
	initial_page_policy: INITIAL_PAGE_POLICY = 'first',
) -> FastAPI:
	router = APIRouter(tags=['fastapi-voyager'])

	@router.get("/dot", response_model=OptionParam)
	def get_dot() -> str:
		voyager = Voyager(module_color=module_color)
		voyager.analysis(target_app)
		dot = voyager.render_dot()

		# include tags and their routes
		tags = voyager.tags

		schemas = voyager.nodes[:]
		schemas.sort(key=lambda s: s.name)

		return OptionParam(
			tags=tags, 
			schemas=schemas,
			dot=dot,
			enable_brief_mode=bool(module_prefix),
			version=__version__,
			swagger_url=swagger_url,
			initial_page_policy=initial_page_policy)

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
		renderer = Renderer(show_fields=core_data.show_fields, module_color=core_data.module_color, schema=core_data.schema)
		return renderer.render_dot(core_data.tags, core_data.routes, core_data.nodes, core_data.links)

	@router.get("/", response_class=HTMLResponse)
	def index():
		index_file = WEB_DIR / "index.html"
		if index_file.exists():
			return index_file.read_text(encoding="utf-8")
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

