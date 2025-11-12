from pydantic import BaseModel, Field
from fastapi import FastAPI
from typing import Optional, Generic, TypeVar
from pydantic_resolve import ensure_subset, Resolver
from tests.service.schema import Story, Task, A
import tests.service.schema as serv
from dataclasses import dataclass

app = FastAPI(title="Demo API", description="A demo FastAPI application for router visualization")

@app.get("/sprints", tags=['for-restapi', 'group_a'], response_model=list[serv.Sprint])
def get_sprint():
    return []

class PageMember(serv.Member):
    fullname: str = ''
    def post_fullname(self):
        return self.first_name + ' ' + self.last_name
    sh: 'Something'  # forward reference

@dataclass
class Something:
    id: int

class TaskA(Task):
    task_type: str = 'A'

class TaskB(Task):
    task_type: str = 'B'


type TaskUnion = TaskA | TaskB
class PageTask(Task):
    owner: Optional[PageMember]

@ensure_subset(Story)
class PageStory(BaseModel):
    id: int
    sprint_id: int
    title: str = Field(exclude=True)

    desc: str = ''
    def post_desc(self):
        return self.title + ' (processed ........................)'

    tasks: list[PageTask] = []
    owner: Optional[PageMember] = None
    union_tasks: list[TaskUnion] = []

class PageSprint(serv.Sprint):
    stories: list[PageStory]
    owner: Optional[PageMember] = None

class PageOverall(BaseModel):
    sprints: list[PageSprint]

class PageOverallWrap(PageOverall):
    content: str

@app.get("/page_overall", tags=['for-page'], response_model=PageOverallWrap)
async def get_page_info():
    page_overall = PageOverallWrap(content="Page Overall Content", sprints=[]) # focus on schema only
    return await Resolver().resolve(page_overall)

class PageStories(BaseModel):
    stories: list[PageStory] 

@app.get("/page_info/", tags=['for-page'], response_model=PageStories)
def get_page_stories():







    







    return {} # no implementation


T = TypeVar('T')
class DataModel(BaseModel, Generic[T]):
    data: T
    id: int

type DataModelPageStory = DataModel[PageStory]

@app.get("/page_test_1/", tags=['for-page'], response_model=DataModelPageStory)
def get_page_test_1():
    return {} # no implementation

@app.get("/page_test_2/", tags=['for-page'], response_model=A)
def get_page_test_2():
    return {}

@app.get("/page_test_3/", tags=['for-page'], response_model=bool)
def get_page_test_3_long_long_long_name():
    return True

@app.get("/page_test_4/", tags=['for-page'])
def get_page_test_3_no_response_model():
    return True

@app.get("/page_test_5/", tags=['long_long_long_tag_name', 'group_b'])
def get_page_test_3_no_response_model():
    return True


for r in app.router.routes:
    r.operation_id = r.name