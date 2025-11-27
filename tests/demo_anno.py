from __future__ import annotations

from typing import Annotated
from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic_resolve import Resolver, ensure_subset

from tests.service.schema.schema import Member, Sprint, Story, Task
from tests.service.schema.extra import A, B 

app = FastAPI(title="Demo API", description="A demo FastAPI application for router visualization")

@app.get("/sprints", tags=['for-restapi'], response_model=list[Sprint])
def get_sprint():
    return []

class PageMember(Member):
    fullname: str = ''
    def post_fullname(self):
        return self.first_name + ' ' + self.last_name

class TaskA(Task):
    task_type: str = 'A'

class TaskB(Task):
    task_type: str = 'B'


type TaskUnion = TaskA | TaskB
class PageTask(Task):
    owner: PageMember | None


class PageOverall(BaseModel):
    sprints: Annotated[list[PageSprint], Field(description="List of sprints")]

class PageSprint(Sprint):
    stories: Annotated[list[PageStory], Field(description="List of stories")]
    owner: Annotated[PageMember | None, Field(description="Owner of the sprint")] = None


@ensure_subset(Story)
class PageStory(BaseModel):
    id: int
    sprint_id: int
    title: str = Field(exclude=True)

    desc: str = ''
    def post_desc(self):
        return self.title + ' (processed)'

    tasks: list[PageTask] = []
    owner: PageMember | None = None
    union_tasks: list[TaskUnion] = []

@app.get("/page_overall", tags=['for-page'], response_model=PageOverall)
async def get_page_info():
    page_overall = PageOverall(sprints=[]) # focus on schema only
    return await Resolver().resolve(page_overall)


# class PageStories(BaseModel):
#     stories: list[PageStory] 

# @app.get("/page_info/", tags=['for-page'], response_model=PageStories)
# def get_page_stories():
#     return {} # no implementation
