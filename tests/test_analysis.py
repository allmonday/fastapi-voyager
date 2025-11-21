
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi_voyager.voyager import Voyager


def test_analysis():

    class B(BaseModel):
        id: int
        value: str

    class A(BaseModel):
        id: int
        name: str
        b: B
    
    class C(BaseModel):
        id: int
        name: str
        b: B

    app = FastAPI()

    @app.get("/test", response_model=A | None)
    def home():
        return None

    @app.get("/test2", response_model=C | None)
    def home2():
        return None

    analytics = Voyager()
    analytics.analysis(app)
    assert len(analytics.nodes) == 3
    assert len(analytics.links) == 6