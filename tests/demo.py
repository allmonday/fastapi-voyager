from dataclasses import dataclass
from typing import Generic, TypeVar, Annotated

from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic_resolve import Resolver, DefineSubset, ExposeAs, SendTo, Collector


from tests.service.schema.schema import Member, Sprint, Story, Task
from tests.service.schema.extra import A
from tests.service.schema.base_entity import BaseEntity

diagram = BaseEntity.get_diagram()

app = FastAPI(title="Demo API", description="A demo FastAPI application for router visualization")

@app.get("/sprints", tags=['for-restapi', 'group_a'], response_model=list[Sprint])
def get_sprint():
    return []

class PageMember(Member):
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
    owner: PageMember | None

class MiddleStory(DefineSubset):
    __subset__ = (Story, ('id', 'sprint_id', 'title'))

class PageStory(DefineSubset):
    __subset__ = (Story, ('id', 'sprint_id'))
    # __subset__ = (Story, ('id', 'sprint_id', 'title:exclude')) # expected behavior, but not supported yet

    title: Annotated[str, ExposeAs('story_title')] = Field(exclude=True)
    def post_title(self):
        return self.title + ' (processed)'

    desc: Annotated[str, ExposeAs('story_desc')] = ''
    def resolve_desc(self):
        return self.desc

    def post_desc(self):
        return self.title + ' (processed ........................)'
    
    

    tasks: Annotated[list[PageTask], SendTo("SomeCollector")] = []
    owner: PageMember | None = None
    def resolve_owner(self):
        return None
    union_tasks: list[TaskUnion] = []

    coll: list[str] = []
    def post_coll(self, c=Collector(alias="top_collector")):
        return c.values()

class PageSprint(Sprint):
    stories: list[PageStory]
    owner: PageMember | None = None

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
def get_page_test_3_no_response_model_long_long_long_name():
    return True


for r in app.router.routes:
    r.operation_id = r.name