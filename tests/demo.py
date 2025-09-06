from fastapi_router_viz.graph import Analytics
from pydantic import BaseModel
from fastapi import FastAPI
from typing import Optional
from pydantic_resolve import ensure_subset
from tests.service import Story, Task
import tests.service as serv

# 创建FastAPI应用实例
app = FastAPI(title="Demo API", description="A demo FastAPI application for router visualization")

@app.get("/sprints", tags=['restapi'], response_model=list[serv.Sprint])
def get_sprint():
    return []

class Member(serv.Member):
    pass

class PageTask(Task):
    owner: Optional[serv.Member]

@ensure_subset(Story)
class PageStory(BaseModel):
    id: int
    sprint_id: int
    title: str

    tasks: list[PageTask] = []
    owner: Optional[Member] = None

class Sprint(serv.Sprint):
    stories: list[PageStory]
    owner: Optional[serv.Member]

class PageOverall(BaseModel):
    sprints: list[Sprint]


@app.get("/page_overall", tags=['page'], response_model=PageOverall)
def get_page_info():
    return {"sprints": []}


class PageStories(BaseModel):
    stories: list[PageStory] 

@app.get("/page_stories/", tags=['page'], response_model=PageStories)
def get_page_info_2():
    return {}

def test_analysis():
    """Test function to demonstrate the analytics"""
    analytics = Analytics()
    analytics.analysis(app)
    print(analytics.generate_dot())


if __name__ == "__main__":
    test_analysis()