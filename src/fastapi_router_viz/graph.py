from fastapi import FastAPI
from fastapi.dependencies.models import ModelField
from fastapi.openapi.utils import get_fields_from_routes
from fastapi_router_viz.type_helper import shelling_type, full_class_name
from pydantic import BaseModel
from fastapi_router_viz.type import FieldInfo, NodeInfo, Node, Link
# read route and schemas, generate graph


class Analytics:
    def __init__(self):
        self.nodes: Node = []
        self.node_set: dict[str, Node] = {}
        self.links: Link = []

    def analysis(self, app: FastAPI):
        """
        1. get routes which return pydantic schema
        2. iterate routes, construct the nodes and links
        """
        _fields = get_fields_from_routes(app.routes)

        schemas = []

        for field in _fields:
            if field.mode == 'serialization':
                schema = shelling_type(field.field_info.annotation)
                if issubclass(schema, BaseModel):
                    schemas.append(schema)

        for s in schemas:
            self.walk_schema(s)

    def add_to_node_set(self, field):
        """
        1. calc full_path, add to node_set
        2. if duplicated, do nothing, else insert
        2. return the full_path
        """
        ...

    def walk_schema(self, schema: BaseModel):
        """
        1. cls is the source, add schema
        2. pydantic fields are targets, add fields and add links
        3. recursively run walk_schema

        """
        ...

    def generate_dot(self):
        """
        """