from __future__ import annotations
from typing import Literal
from pydantic import BaseModel
from pydantic_resolve import Relationship
from .base_entity import BaseEntity



class Member(BaseModel):
    id: int
    first_name: str
    last_name: str

class Task(BaseModel, BaseEntity):
    __pydantic_resolve_relationships__ = [
         Relationship(field='owner_id', target_kls=Member),
    ]
    id: int
    story_id: int
    description: str
    owner_id: int

class Story(BaseModel, BaseEntity):
    __pydantic_resolve_relationships__ = [Relationship(field='id', target_kls=list[Task]) ]
    id: int
    type: Literal['feature', 'bugfix']
    dct: dict
    sprint_id: int
    title: str
    description: str

class Sprint(BaseModel, BaseEntity):
    __pydantic_resolve_relationships__ = [Relationship(field='id', target_kls=list[Story]) ]
    id: int
    name: str
