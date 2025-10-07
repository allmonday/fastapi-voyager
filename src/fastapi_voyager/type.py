from dataclasses import dataclass, field
from typing import Literal

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
    source_code: str = ''
    vscode_link: str = ''  # optional vscode deep link

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

LinkType = Literal['internal', 'parent', 'entry', 'subset']

@dataclass
class Link:
    """
    type: 
        - entry: tag -> route, route -> response model
        - subset: schema -> schema (subset)
        - parent: schema -> schema (inheritance)
        - internal: schema -> schema (field reference)
    """
    # node + field level links
    source: str
    target: str

    # node level links
    source_origin: str
    target_origin: str
    type: LinkType
