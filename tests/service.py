from fastapi_router_viz.graph import Analytics
from pydantic import BaseModel
from fastapi import FastAPI
from typing import Optional
from pydantic_resolve import ensure_subset

class Sprint(BaseModel):
    id: int
    name: str

class Story(BaseModel):
    id: int
    sprint_id: int
    title: str

class Task(BaseModel):
    id: int
    story_id: int
    description: str
    owner_id: int

class Member(BaseModel):
    id: int
    username: str

