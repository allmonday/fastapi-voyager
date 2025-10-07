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

@dataclass
class Link:
    source: str
    source_origin: str  # internal relationship
    target: str
    target_origin: str
    type: Literal['child', 'parent', 'entry', 'subset']
