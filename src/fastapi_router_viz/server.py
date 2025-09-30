from pathlib import Path
from typing import Optional, Dict
from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi_router_viz.graph import Analytics
from fastapi_router_viz.type import Tag, FieldInfo


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

	app = FastAPI(title="fastapi-router-viz demo server")

	# Enable gzip compression for larger responses (e.g. DOT / schemas payload)
	if gzip_minimum_size is not None and gzip_minimum_size >= 0:
		app.add_middleware(GZipMiddleware, minimum_size=gzip_minimum_size)

	@app.get("/dot", response_model=OptionParam)
	def get_dot() -> str:
		analytics = Analytics(module_color=module_color, load_meta=True)
		analytics.analysis(target_app)
		dot = analytics.generate_dot()

		# include tags and their routes
		tags = analytics.tags

		schemas = [
			SchemaType(
				name=s.name,
				fullname=s.id,
				fields=s.fields,
				source_code=s.source_code,
				vscode_link=s.vscode_link
			) for s in analytics.nodes
		]
		schemas.sort(key=lambda s: s.name)

		return OptionParam(tags=tags, schemas=schemas, dot=dot)

	@app.post("/dot", response_class=PlainTextResponse)
	def get_filtered_dot(payload: Payload) -> str:
		analytics = Analytics(
			include_tags=payload.tags,
			schema=payload.schema_name,
			schema_field=payload.schema_field,
			show_fields=payload.show_fields,
			module_color=module_color,
			route_name=payload.route_name,
			load_meta=False,
		)
		analytics.analysis(target_app)
		return analytics.generate_dot()

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
		  <p>index.html not found. Create one under src/fastapi_router_viz/web/index.html</p>
		</body>
		</html>
		"""

	# Serve static files under /static
	app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

	return app

