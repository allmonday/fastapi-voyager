from fastapi_router_viz.graph import analysis
from pydantic import BaseModel
from fastapi import FastAPI
from typing import Optional


def test_analysis():

    class B(BaseModel):
        id: int
        value: str

    class A(BaseModel):
        id: int
        name: str
        b: B

    app = FastAPI()

    @app.get("/test", response_model=Optional[A])
    def home():
        return None

    assert analysis(app) == 1
