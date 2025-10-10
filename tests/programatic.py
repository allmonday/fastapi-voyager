from fastapi import FastAPI
from fastapi_voyager.server import create_app_with_fastapi
from tests.demo import app as demo_app

subapp = create_app_with_fastapi(demo_app)

app = FastAPI()
app.mount("/xxx", subapp)
