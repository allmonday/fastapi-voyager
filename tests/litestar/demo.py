from dataclasses import dataclass
from typing import Annotated, Generic, TypeVar

from litestar import Controller, get
from pydantic import BaseModel, Field
from pydantic_resolve import Collector, DefineSubset, ExposeAs, Resolver, SendTo

from tests.service.schema.base_entity import BaseEntity
from tests.service.schema.extra import A
from tests.service.schema.schema import Member, Sprint, Story, Task

diagram = BaseEntity.get_diagram()


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


class PageStories(BaseModel):
    stories: list[PageStory]


T = TypeVar('T')


class DataModel(BaseModel, Generic[T]):
    data: T
    id: int


type DataModelPageStory = DataModel[PageStory]


class DemoController(Controller):
    path = "/demo"

    @get("/sprints", tags=['for-restapi', 'group_a'])
    def get_sprints(self) -> list[Sprint]:
        return []

    @get("/page_overall", tags=['for-ui-page'])
    async def get_page_info(self) -> PageOverallWrap:
        page_overall = PageOverallWrap(content="Page Overall Content", sprints=[])
        return await Resolver().resolve(page_overall)

    @get("/page_info/", tags=['for-ui-page'])
    def get_page_stories(self) -> PageStories:
        return {}

    @get("/page_test_1/", tags=['for-ui-page'])
    def get_page_test_1(self) -> DataModelPageStory:
        return {}

    @get("/page_test_2/", tags=['for-ui-page'])
    def get_page_test_2(self) -> A:
        return {}

    @get("/page_test_3/", tags=['for-ui-page'])
    def get_page_test_3_long_long_long_name(self) -> bool:
        return True

    @get("/page_test_4/", tags=['for-ui-page'])
    def get_page_test_3_no_response_model(self) -> bool:
        return True

    @get("/page_test_5/", tags=['long_long_long_tag_name', 'group_b'])
    def get_page_test_3_no_response_model_long_long_long_name(self) -> bool:
        return True
