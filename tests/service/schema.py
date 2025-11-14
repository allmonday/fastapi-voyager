from pydantic import BaseModel
from typing import Literal, Dict

class Sprint(BaseModel):
    id: int
    name: str

class Story(BaseModel):
    id: int
    type: Literal['feature', 'bugfix']
    dct: Dict
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