from dataclasses import dataclass
import uuid


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
    id: uuid.UUID
    name: str
    node_info: NodeInfo


class Link:
    source: uuid.UUID
    target: uuid.UUID
