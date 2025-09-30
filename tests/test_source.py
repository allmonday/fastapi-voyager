import inspect
from dataclasses import dataclass
from pydantic_resolve import ensure_subset
from pydantic import BaseModel, Field

class A(BaseModel):
    id: int
    name: str


@ensure_subset(A)
class B(BaseModel):
    id: int


code = inspect.getsource(B)
print(code)