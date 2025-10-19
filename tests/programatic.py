from fastapi_voyager.server import create_app_with_fastapi
from tests.demo import app

app.mount('/voyager', create_app_with_fastapi(app, module_color={"tests.service": "red"}, module_prefix="tests.service"))
