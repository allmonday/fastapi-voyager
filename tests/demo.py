from fastapi_router_viz.graph import Analytics
from pydantic import BaseModel
from fastapi import FastAPI
from typing import Optional
from pydantic_resolve import ensure_subset
from tests.service import Sprint, Story, Task, Member

# 创建FastAPI应用实例
app = FastAPI(title="Demo API", description="A demo FastAPI application for router visualization")

@app.get("/sprints", tags=['restapi'], response_model=list[Sprint])
def get_sprint():
    """Get A model data"""
    return None


class PageTask(Task):
    owner: Optional[Member]

class PageStory(Story):
    tasks: list[PageTask]
    owner: Optional[Member]

class PageSprint(Sprint):
    stories: list[PageStory]
    owner: Optional[Member]

class PageInfo(BaseModel):
    sprints: list[PageSprint]

@app.get("/page_info", tags=['page'], response_model=PageInfo)
def get_page_info():
    return {"sprints": []}

def test_analysis():
    """Test function to demonstrate the analytics"""
    analytics = Analytics()
    analytics.analysis(app)
    print(analytics.generate_dot())


if __name__ == "__main__":
    test_analysis()