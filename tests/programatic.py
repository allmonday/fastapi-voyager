from fastapi_voyager import create_voyager
from tests.demo import app

app.mount('/voyager', create_voyager(app, module_color={"tests.service": "red"}, module_prefix="tests.service"))
# app.mount('/voyager', create_voyager(app, module_color={"tests.service": "red"}))
