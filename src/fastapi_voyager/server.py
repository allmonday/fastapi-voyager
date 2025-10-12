from pathlib import Path
from typing import Optional
from fastapi import FastAPI, APIRouter
from starlette.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi_voyager.voyager import Voyager
from fastapi_voyager.type import Tag, FieldInfo, CoreData
from fastapi_voyager.render import Renderer


WEB_DIR = Path(__file__).parent / "web"
WEB_DIR.mkdir(exist_ok=True)

class SchemaType(BaseModel):
	name: str
	fullname: str
	source_code: str
	vscode_link: str
	fields: list[FieldInfo]

class OptionParam(BaseModel):
	tags: list[Tag]
	schemas: list[SchemaType]
	dot: str

class Payload(BaseModel):
	tags: Optional[list[str]] = None
	schema_name: Optional[str] = None
	schema_field: Optional[str] = None
	route_name: Optional[str] = None
	show_fields: str = 'object'
	show_meta: bool = False
	brief: bool = False

def create_route(
	target_app: FastAPI,
	module_color: dict[str, str] | None = None,
	module_prefix: Optional[str] = None,
):
	router = APIRouter(tags=['fastapi-voyager'])

	@router.get("/dot", response_model=OptionParam)
	def get_dot() -> str:
		voyager = Voyager(module_color=module_color, load_meta=True)
		voyager.analysis(target_app)
		dot = voyager.render_dot()

		# include tags and their routes
		tags = voyager.tags

		schemas = [
			SchemaType(
				name=s.name,
				fullname=s.id,
				fields=s.fields,
				source_code=s.source_code,
				vscode_link=s.vscode_link
			) for s in voyager.nodes
		]
		schemas.sort(key=lambda s: s.name)

		return OptionParam(tags=tags, schemas=schemas, dot=dot)

	@router.post("/dot", response_class=PlainTextResponse)
	def get_filtered_dot(payload: Payload) -> str:
		voyager = Voyager(
			include_tags=payload.tags,
			schema=payload.schema_name,
			schema_field=payload.schema_field,
			show_fields=payload.show_fields,
			module_color=module_color,
			route_name=payload.route_name,
			load_meta=False,
		)
		voyager.analysis(target_app)
		if payload.brief:
			return voyager.render_brief_dot(module_prefix=module_prefix)
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
			load_meta=False,
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

	return router


def create_app_with_fastapi(
	target_app: FastAPI,
	module_color: dict[str, str] | None = None,
	gzip_minimum_size: int | None = 500,
	module_prefix: Optional[str] = None,
) -> FastAPI:
	router = create_route(target_app, module_color=module_color, module_prefix=module_prefix)

	app = FastAPI(title="fastapi-voyager demo server")
	if gzip_minimum_size is not None and gzip_minimum_size >= 0:
		app.add_middleware(GZipMiddleware, minimum_size=gzip_minimum_size)

	app.mount("/fastapi-voyager-static", StaticFiles(directory=str(WEB_DIR)), name="static")
	app.include_router(router)

	return app

