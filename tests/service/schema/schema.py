from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field
from pydantic_resolve import Relationship, MultipleRelationship, Link
from .base_entity import BaseEntity



class Member(BaseModel):
    id: int
    first_name: str
    last_name: str

class Task(BaseModel, BaseEntity):
    __pydantic_resolve_relationships__ = [
        Relationship(field='owner_id', target_kls=Member),
        Relationship(field='story_id', target_kls='Story'),
    ]
    id: int = Field(description="The unique identifier of the task")
    story_id: int
    description: str
    owner_id: int

class Story(BaseModel, BaseEntity):
    __pydantic_resolve_relationships__ = [
        Relationship(field='id', target_kls=list[Task]),
    ]
    id: int
    type: Literal['feature', 'bugfix']
    dct: dict
    sprint_id: int
    title: str
    description: str

class Sprint(BaseModel, BaseEntity):
    __pydantic_resolve_relationships__ = [
        MultipleRelationship(field='id', target_kls=list[Story], links=[
            Link(biz='all', loader=lambda x: x),
            Link(biz='done', loader=lambda x: x),
        ]) 
    ]
    id: int
    name: str