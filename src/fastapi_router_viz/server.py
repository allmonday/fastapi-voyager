from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles


WEB_DIR = Path(__file__).parent / "web"
WEB_DIR.mkdir(exist_ok=True)

app = FastAPI(title="fastapi-router-viz demo server")

# --- DOT source configuration ---
_DOT_TEXT: Optional[str] = None


def configure_dot_source(dot_text: Optional[str] = None) -> None:
	global _DOT_TEXT
	_DOT_TEXT = dot_text

@app.get("/dot", response_class=PlainTextResponse)
def get_dot() -> str:
	"""Return DOT graph string from configured source; fallback to a->b."""
	if _DOT_TEXT is not None:
		return _DOT_TEXT
	return "digraph G { a -> b }"

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

# Optionally serve static files under /static if you add assets later
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

