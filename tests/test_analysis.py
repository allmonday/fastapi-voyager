
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


def test_analysis_with_non_class_response_model():
    """Regression test for TypeError: issubclass() arg 1 must be a class.

    Real-world trigger: a route uses a PEP 695 type alias as response_model, e.g.
        type ResourceActionDict = dict[AccessResourceUnion, set[AccessActionUnion]]
    FastAPI infers response_model from the return annotation. get_core_types() unwraps
    the type alias to dict[X, set[Y]] (a types.GenericAlias), which is not a class.

    Python version behavior difference:
    - Python 3.12: issubclass(dict[X, Y], BaseModel) returns False (no error)
    - Python 3.13: issubclass(dict[X, Y], BaseModel) raises TypeError

    In Pydantic <= 2.11, ModelMetaclass.__subclasscheck__ (pure-Python) masks this
    via hasattr short-circuit. In Pydantic >= 2.13 (compiled Rust extension), the
    guard no longer catches all GenericAlias types, exposing the bug on Python 3.13.

    We patch out __subclasscheck__ to simulate the Python 3.13 + Pydantic 2.13 behavior.
    """
    from unittest.mock import patch
    from typing import Callable
    from pydantic._internal._model_construction import ModelMetaclass
    from enum import Enum

    class ResourceEnum(str, Enum):
        FILE = "file"

    class ActionEnum(str, Enum):
        READ = "read"

    ResourceActionDict = dict[ResourceEnum, set[ActionEnum]]

    app = FastAPI()

    @app.get("/permissions", response_model=ResourceActionDict)
    def get_permissions():
        return {}

    @app.get("/callback", response_model=Callable[[int], str])
    def callback_endpoint():
        pass

    with patch.object(ModelMetaclass, '__subclasscheck__', type.__subclasscheck__):
        voyager = Voyager()
        voyager.analysis(app)
        assert len(voyager.nodes) == 0