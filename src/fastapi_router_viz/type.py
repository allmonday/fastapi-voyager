from dataclasses import dataclass
from typing import Literal


@dataclass
class FieldInfo:
    name: str
    type_name: str

@dataclass
class Tag:
    id: str
    name: str

@dataclass
class Route:
    id: str
    name: str

@dataclass
class SchemaNode:
    id: str
    module: str
    name: str
    fields: list[FieldInfo]

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
