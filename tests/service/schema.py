from fastapi_voyager.voyager import Voyager
from pydantic import BaseModel
from pydantic_resolve import ensure_subset

class Sprint(BaseModel):
    id: int
    name: str

class Story(BaseModel):
    id: int
    sprint_id: int
    title: str
    description: str

class Task(BaseModel):
    id: int
    story_id: int
    description: str
    owner_id: int

class Member(BaseModel):
    id: int
    first_name: str
    last_name: str


class B(BaseModel):
    id: int

class A(BaseModel):
    id: int
    b: B