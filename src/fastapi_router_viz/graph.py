from typing import Literal
from fastapi import FastAPI, routing
from fastapi.openapi.utils import get_fields_from_routes
from fastapi_router_viz.type_helper import shelling_type, full_class_name
from pydantic import BaseModel
from fastapi_router_viz.type import Route, NodeInfo, Node, Link
# read route and schemas, generate graph


class Analytics:
    def __init__(self):
        self.routes: list[str] = []
        self.nodes: list[Node] = []
        self.node_set: dict[str, Node] = {}
        self.link_set: set[tuple[str, str]] = set()
        self.links: list[Link] = []

    def analysis(self, app: FastAPI):
        """
        1. get routes which return pydantic schema
        2. iterate routes, construct the nodes and links
        """
        _fields = get_fields_from_routes(app.routes)

        schemas: list[type[BaseModel]] = []

        for field in _fields:
            if field.mode == 'serialization':
                schema = shelling_type(field.field_info.annotation)
                if schema and issubclass(schema, BaseModel):

                    route_name = f'router: {field.name.replace('Response_','')}'
                    self.routes.append(route_name)
                    self.links.append(Link(
                        source=route_name,
                        target=full_class_name(schema),
                        type='entry'
                    ))

                    schemas.append(schema)

        for s in schemas:
            self.walk_schema(s)
        
        self.nodes = list(self.node_set.values())


    def add_to_node_set(self, schema):
        """
        1. calc full_path, add to node_set
        2. if duplicated, do nothing, else insert
        2. return the full_path
        """
        full_name = full_class_name(schema)
        if full_name not in self.node_set:
            self.node_set[full_name] = Node(
                id=full_name, 
                name=schema.__name__,
                node_info=NodeInfo(
                    is_entry=False,
                    router_name="xxx",
                    fields=[]
                )
            )
        return full_name

    def add_to_link_set(self, source: str, target: str, type: Literal['child', 'parent']):
        """
        1. add link to link_set
        2. if duplicated, do nothing, else insert
        """
        pair = (source, target)
        if result := pair not in self.link_set:
            self.link_set.add(pair)
            self.links.append(Link(
                source=source,
                target=target,
                type=type
            ))
        return result

    def walk_schema(self, schema: type[BaseModel]):
        """
        1. cls is the source, add schema
        2. pydantic fields are targets, if annotation is subclass of BaseMode, add fields and add links
        3. recursively run walk_schema
        """
        self.add_to_node_set(schema)

        # if schema has inherit
        for base in schema.__bases__:
            if issubclass(base, BaseModel) and base is not BaseModel:
                self.add_to_node_set(base)
                self.add_to_link_set(full_class_name(schema), full_class_name(base), type='parent')

        for k, v in schema.model_fields.items():
            anno = shelling_type(v.annotation)
            if anno and issubclass(anno, BaseModel):
                self.add_to_node_set(v.annotation)

                if self.add_to_link_set(full_class_name(schema), full_class_name(v.annotation), type='child'):
                    self.walk_schema(anno)


    def generate_dot(self):
        """
        """
        def _get_link_style(link: Link):
            if link.type == 'child':
                return 'dashed'
            elif link.type == 'parent':
                return 'solid'
            elif link.type == 'entry':
                return 'bold'
            return 'solid'

        routes = [
            f'''
            "{r}" [
                label = "{r}"
                shape = "record"
                fillcolor = "lightgreen"
                style = "filled"
            ];''' for r in self.routes]
        route_str = '\n'.join(routes)

        nodes = [
            f'''
            "{node.id}" [
                label = "{node.name}"
                shape = "record"
            ];''' for node in self.nodes]
        node_str = '\n'.join(nodes)

        links = [
            f'''"{link.source}" -> "{link.target}" [ style = "{_get_link_style(link)}" ];''' for link in self.links
        ]
        link_str = '\n'.join(links)

        template = f'''
        digraph mygraph {{
            fontname="Helvetica,Arial,sans-serif"
            node [fontname="Helvetica,Arial,sans-serif"]
            edge [fontname="Helvetica,Arial,sans-serif"]
            graph [
                rankdir = "LR"
            ];
            node [
                fontsize = "16"
            ];
            {route_str}
            {node_str}
            {link_str}
            }}
        '''
        return template