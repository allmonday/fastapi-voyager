import os

import django

# Configure Django settings before importing django-ninja
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.django_ninja.settings')
django.setup()

from dataclasses import dataclass
from typing import Annotated, Generic, TypeVar

from ninja import NinjaAPI
from pydantic import BaseModel, Field
from pydantic_resolve import Collector, DefineSubset, ExposeAs, Resolver, SendTo

from tests.service.schema.base_entity import BaseEntity
from tests.service.schema.extra import A
from tests.service.schema.schema import Member, Sprint, Story, Task

diagram = BaseEntity.get_diagram()

# Create Django Ninja API instance
api = NinjaAPI(title="Demo API (Django Ninja)", description="A demo Django Ninja application for router visualization")


@api.get("/sprints", tags=['for-restapi', 'group_a'])
def get_sprints(request) -> list[Sprint]:
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
    owner: PageMember | None = None


class MiddleStory(DefineSubset):
    __subset__ = (Story, ('id', 'sprint_id', 'title'))


class PageStory(DefineSubset):
    __subset__ = (Story, ('id', 'sprint_id'))

    title: Annotated[str, ExposeAs('story_title')] = Field(exclude=True)
    def post_title(self):
        return self.title + ' (processed)'

    desc: Annotated[str, ExposeAs('story_desc')] = ''
    def resolve_desc(self):
        return self.desc

    def post_desc(self):
        return self.title + ' (processed........................)'

    tasks: Annotated[list[PageTask], SendTo("SomeCollector")] = []

    coll: list[str] = []
    def post_coll(self, c=Collector(alias="top_collector")):
        return c.values()


class PageSprint(Sprint):
    stories: list[PageStory]


class PageOverall(BaseModel):
    sprints: list[PageSprint]


class PageOverallWrap(PageOverall):
    content: str

    all_tasks: list[PageTask] = []
    def post_all_tasks(self, collector=Collector(alias="SomeCollector")):
        return collector.values()


@api.get("/page_overall", tags=['for-ui-page'])
async def get_page_info(request) -> PageOverallWrap:
    page_overall = PageOverallWrap(content="Page Overall Content", sprints=[])
    return await Resolver().resolve(page_overall)


class PageStories(BaseModel):
    stories: list[PageStory]


@api.get("/page_info/", tags=['for-ui-page'])
def get_page_stories(request) -> PageStories:
    return {}


T = TypeVar('T')


class DataModel(BaseModel, Generic[T]):
    data: T
    id: int


type DataModelPageStory = DataModel[PageStory]


@api.get("/page_test_1/", tags=['for-ui-page'])
def get_page_test_1(request) -> DataModelPageStory:
    return {}


@api.get("/page_test_2/", tags=['for-ui-page'])
def get_page_test_2(request) -> A:
    return {}


@api.get("/page_test_3/", tags=['for-ui-page'])
def get_page_test_3_long_long_long_name(request) -> bool:
    return True


@api.get("/page_test_4/", tags=['for-ui-page'])
def get_page_test_3_no_response_model(request):
    return True


@api.get("/page_test_5/", tags=['long_long_long_tag_name', 'group_b'])
def get_page_test_3_no_response_model_long_long_long_name(request):
    return True


# Note: Django Ninja doesn't have operation_id attribute like FastAPI
# The introspector will generate it from the function name
