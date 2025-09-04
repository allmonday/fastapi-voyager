from dataclasses import dataclass
from typing import Literal


@dataclass
class FieldInfo:
    name: str
    type_name: str


@dataclass
class NodeInfo:
    is_entry: bool
    router_name: str
    fields: list[FieldInfo]


@dataclass
class Node:
    id: str
    name: str
    node_info: NodeInfo


@dataclass
class Route:
    id: str
    name: str

@dataclass
class Link:
    source: str
    target: str
    type: Literal['child', 'parent', 'entry', 'subset']
