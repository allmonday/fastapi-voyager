from dataclasses import dataclass
from typing import Annotated, Generic, Optional, TypeVar

from litestar import Controller, Litestar, Request, Response, get, post
from litestar.handlers import HTTPRouteHandler
from pydantic import BaseModel, Field
from pydantic_resolve import (
    Collector,
    DefineSubset,
    ExposeAs,
    GraphQLHandler,
    Resolver,
    SchemaBuilder,
    SendTo,
    config_global_resolver,
)

from tests.service.schema.base_entity import BaseEntity
from tests.service.schema.extra import A
from tests.service.schema.schema import Member, Sprint, Story, Task

diagram = BaseEntity.get_diagram()

# 创建 AutoLoad 工厂（v4: 从 diagram 实例创建）
AutoLoad = diagram.create_auto_load()

# 配置全局 resolver
config_global_resolver(diagram)

# 创建 GraphQL handler 和 schema builder
graphql_handler = GraphQLHandler(diagram, enable_from_attribute_in_type_adapter=True)
schema_builder = SchemaBuilder(diagram)


# =====================================
# GraphQL Support
# =====================================

class GraphQLRequest(BaseModel):
    query: str
    operationName: Optional[str] = None


# GraphiQL Playground HTML
GRAPHIQL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GraphiQL - Litestar Demo</title>
  <style>
    body { margin: 0; }
    #graphiql { height: 100dvh; }
    .loading {
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 2rem;
    }
  </style>
  <link rel="stylesheet" href="https://esm.sh/graphiql/dist/style.css" />
  <link rel="stylesheet" href="https://esm.sh/@graphiql/plugin-explorer/dist/style.css" />
  <script type="importmap">
    {
      "imports": {
        "react": "https://esm.sh/react@19.1.0",
        "react/jsx-runtime": "https://esm.sh/react@19.1.0/jsx-runtime",
        "react-dom": "https://esm.sh/react-dom@19.1.0",
        "react-dom/client": "https://esm.sh/react-dom@19.1.0/client",
        "@emotion/is-prop-valid": "data:text/javascript,",
        "graphiql": "https://esm.sh/graphiql?standalone&external=react,react-dom,@graphiql/react,graphql",
        "graphiql/": "https://esm.sh/graphiql/",
        "@graphiql/plugin-explorer": "https://esm.sh/@graphiql/plugin-explorer?standalone&external=react,@graphiql/react,graphql",
        "@graphiql/react": "https://esm.sh/@graphiql/react?standalone&external=react,react-dom,graphql,@emotion/is-prop-valid",
        "@graphiql/toolkit": "https://esm.sh/@graphiql/toolkit?standalone&external=graphql",
        "graphql": "https://esm.sh/graphql@16.11.0"
      }
    }
  </script>
</head>
<body>
  <div id="graphiql">
    <div class="loading">Loading…</div>
  </div>
  <script type="module">
    import React from 'react';
    import ReactDOM from 'react-dom/client';
    import { GraphiQL, HISTORY_PLUGIN } from 'graphiql';
    import { createGraphiQLFetcher } from '@graphiql/toolkit';
    import { explorerPlugin } from '@graphiql/plugin-explorer';

    const fetcher = createGraphiQLFetcher({ url: '/graphql' });
    const plugins = [HISTORY_PLUGIN, explorerPlugin()];

    function App() {
      return React.createElement(GraphiQL, {
        fetcher: fetcher,
        plugins: plugins,
      });
    }

    const container = document.getElementById('graphiql');
    const root = ReactDOM.createRoot(container);
    root.render(React.createElement(App));
  </script>
</body>
</html>
"""


# =====================================
# GraphQL Controllers (root path)
# =====================================

class GraphQLController(Controller):
    """GraphQL endpoints at root path"""
    path = ""

    @get("/graphql", tags=['graphql'])
    async def graphiql_playground(self) -> Response[str]:
        """GraphiQL 交互式查询界面"""
        return Response(content=GRAPHIQL_HTML, media_type="text/html")

    @post("/graphql", tags=['graphql'])
    async def graphql_endpoint(self, data: GraphQLRequest) -> dict:
        """GraphQL 查询端点"""
        result = await graphql_handler.execute(query=data.query)
        return result

    @get("/graphql/schema", tags=['graphql'])
    async def graphql_schema(self) -> Response[str]:
        """GraphQL Schema 端点（返回 SDL 格式）"""
        schema_sdl = schema_builder.build_schema()
        return Response(content=schema_sdl, media_type="text/plain; charset=utf-8")


# =====================================
# Page Models
# =====================================

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
    owner: Annotated[PageMember | None, AutoLoad()] = None


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

    tasks: Annotated[list[PageTask], AutoLoad(), SendTo("SomeCollector")] = []

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

    @get("/sprints", tags=['for-restapi', 'group_a'], sync_to_thread=False)
    def get_sprints(self) -> list[Sprint]:
        return []

    @get("/page_overall", tags=['for-ui-page'])
    async def get_page_info(self) -> PageOverallWrap:
        page_overall = PageOverallWrap(content="Page Overall Content", sprints=[])
        return await Resolver().resolve(page_overall)

    @get("/page_info/", tags=['for-ui-page'], sync_to_thread=False)
    def get_page_stories(self) -> PageStories:
        return {}

    @get("/page_test_1/", tags=['for-ui-page'], sync_to_thread=False)
    def get_page_test_1(self) -> DataModelPageStory:
        return {}

    @get("/page_test_2/", tags=['for-ui-page'], sync_to_thread=False)
    def get_page_test_2(self) -> A:
        return {}

    @get("/page_test_3/", tags=['for-ui-page'], sync_to_thread=False)
    def get_page_test_3_long_long_long_name(self) -> bool:
        return True

    @get("/page_test_4/", tags=['for-ui-page'], sync_to_thread=False)
    def get_page_test_3_no_response_model(self) -> bool:
        return True

    @get("/page_test_5/", tags=['long_long_long_tag_name', 'group_b'], sync_to_thread=False)
    def get_page_test_3_no_response_model_long_long_long_name(self) -> bool:
        return True


# Export route handlers for extension (e.g., adding voyager)
ROUTE_HANDLERS = [GraphQLController, DemoController]

# Create a Litestar app instance - this is the main app that can be run directly
app = Litestar(
    route_handlers=ROUTE_HANDLERS
)
