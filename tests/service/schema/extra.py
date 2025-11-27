from pydantic import BaseModel

class B(BaseModel):
    id: int

class A(BaseModel):
    id: int
    b: B