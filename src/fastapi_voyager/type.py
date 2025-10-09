from dataclasses import field
from pydantic.dataclasses import dataclass
from typing import Literal, Optional

@dataclass
class NodeBase:
    id: str
    name: str

@dataclass
class FieldInfo:
    name: str
    type_name: str
    from_base: bool = False
    is_object: bool = False
    is_exclude: bool = False

@dataclass
class Tag(NodeBase):
    routes: list['Route']  # route.id

@dataclass
class Route(NodeBase):
    module: str
    source_code: str = ''
    vscode_link: str = ''  # optional vscode deep link

@dataclass
class ModuleRoute:
    name: str
    fullname: str
    routes: list[Route]
    modules: list['ModuleRoute']

@dataclass
class SchemaNode(NodeBase):
    module: str
    source_code: str = ''  # optional for tests / backward compatibility
    vscode_link: str = ''  # optional vscode deep link
    fields: list[FieldInfo] = field(default_factory=list)

@dataclass
class ModuleNode:
    name: str
    fullname: str
    schema_nodes: list[SchemaNode]
    modules: list['ModuleNode']


# type: 
#    - tag_route: tag -> route
#    - route_to_schema: route -> response model
#    - subset: schema -> schema (subset)
#    - parent: schema -> schema (inheritance)
#    - schema: schema -> schema (field reference)
LinkType = Literal['schema', 'parent', 'tag_route', 'subset', 'route_to_schema']

@dataclass
class Link:
    # node + field level links
    source: str
    target: str

    # node level links
    source_origin: str
    target_origin: str
    type: LinkType

FieldType = Literal['single', 'object', 'all']
PK = "PK"

@dataclass
class CoreData:
    tags: list[Tag]
    routes: list[Route]
    nodes: list[SchemaNode]
    links: list[Link]
    show_fields: FieldType
    module_color: Optional[dict[str, str]] = None
    schema: Optional[str] = None