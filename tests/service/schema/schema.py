from typing import Literal

from pydantic import BaseModel


class Sprint(BaseModel):
    id: int
    name: str

class Story(BaseModel):
    id: int
    type: Literal['feature', 'bugfix']
    dct: dict
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

