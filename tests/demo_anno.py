from __future__ import annotations
from pydantic import BaseModel, Field
from fastapi import FastAPI
from typing import Optional
from pydantic_resolve import ensure_subset, Resolver
from tests.service.schema import Story, Task
import tests.service.schema as serv

app = FastAPI(title="Demo API", description="A demo FastAPI application for router visualization")

@app.get("/sprints", tags=['for-restapi'], response_model=list[serv.Sprint])
def get_sprint():
    return []

class Tree(BaseModel):
    id: int
    name: str
    children: list[Tree] = []

class PageMember(serv.Member):
    fullname: str = ''
    def post_fullname(self):
        return self.first_name + ' ' + self.last_name

class TaskA(Task):
    task_type: str = 'A'

class TaskB(Task):
    task_type: str = 'B'


type TaskUnion = TaskA | TaskB
class PageTask(Task):
    owner: Optional[PageMember]


class PageOverall(BaseModel):
    sprints: list[PageSprint]

class PageSprint(serv.Sprint):
    stories: list[PageStory]
    owner: Optional[PageMember] = None


@ensure_subset(Story)
class PageStory(BaseModel):
    id: int
    sprint_id: int
    title: str = Field(exclude=True)

    desc: str = ''
    def post_desc(self):
        return self.title + ' (processed)'

    tasks: list[PageTask] = []
    owner: Optional[PageMember] = None
    union_tasks: list[TaskUnion] = []

@app.get("/page_overall", tags=['for-page'], response_model=PageOverall)
async def get_page_info():
    page_overall = PageOverall(sprints=[]) # focus on schema only
    return await Resolver().resolve(page_overall)


class PageStories(BaseModel):
    stories: list[PageStory] 

@app.get("/page_info/", tags=['for-page'], response_model=PageStories)
def get_page_stories():
    return {} # no implementation

@app.get("/rest-tree/", tags=['for-restapi'], response_model=Tree)
def get_tree():
    return {} # no implementation