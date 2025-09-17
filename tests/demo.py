from fastapi_router_viz.graph import Analytics
from pydantic import BaseModel
from fastapi import FastAPI
from typing import Optional, Union
from pydantic_resolve import ensure_subset
from tests.service import Story, Task
import tests.service as serv

app = FastAPI(title="Demo API", description="A demo FastAPI application for router visualization")

@app.get("/sprints", tags=['for-restapi'], response_model=list[serv.Sprint])
def get_sprint():
    return []

class PageTask(Task):
    owner: Optional[serv.Member]

@ensure_subset(Story)
class PageStory(BaseModel):
    id: int
    sprint_id: int
    title: str

    tasks: list[PageTask] = []
    owner: Optional[serv.Member] = None

class PageSprint(serv.Sprint):
    stories: list[PageStory]
    owner: Optional[serv.Member] = None

class PageOverall(BaseModel):
    sprints: list[PageSprint]


@app.get("/page_overall", tags=['for-page'], response_model=PageOverall)
def get_page_info():
    return {"sprints": []}


class PageStories(BaseModel):
    stories: list[PageStory] 

@app.get("/page_info/", tags=['for-page'], response_model=PageStories)
def get_page_stories():
    return {} # no implementation