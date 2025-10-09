from pathlib import Path
from typing import Optional
from fastapi import FastAPI
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

def create_app_with_fastapi(
	target_app: FastAPI,
	module_color: dict[str, str] | None = None,
	gzip_minimum_size: int | None = 500,
) -> FastAPI:
	"""Create a FastAPI server that serves DOT computed via Analytics.

	This avoids module-level globals by keeping state in closures.
	"""

	app = FastAPI(title="fastapi-voyager demo server")

	# Enable gzip compression for larger responses (e.g. DOT / schemas payload)
	if gzip_minimum_size is not None and gzip_minimum_size >= 0:
		app.add_middleware(GZipMiddleware, minimum_size=gzip_minimum_size)

	@app.get("/dot", response_model=OptionParam)
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

	@app.post("/dot", response_class=PlainTextResponse)
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
		return voyager.render_dot()

	@app.post("/dot-core-data", response_model=CoreData)
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
	
	@app.post('/dot-render-core-data', response_class=PlainTextResponse)
	def render_dot_from_core_data(core_data: CoreData) -> str:
		renderer = Renderer(show_fields=core_data.show_fields, module_color=core_data.module_color, schema=core_data.schema)
		return renderer.render_dot(core_data.tags, core_data.routes, core_data.nodes, core_data.links)

	@app.get("/", response_class=HTMLResponse)
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

	# Serve static files under /static
	app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

	return app

