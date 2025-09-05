from typing import Literal
from fastapi import FastAPI, routing
from fastapi_router_viz.type_helper import get_core_types, full_class_name
from pydantic import BaseModel
from fastapi_router_viz.type import Route, NodeInfo, Node, Link
from pydantic_resolve.constant import ENSURE_SUBSET_REFERENCE
# read route and schemas, generate graph


class Analytics:
    def __init__(
            self, 
            model_prefixs: list[str] | None = None):

        self.routes: list[Route] = []

        self.nodes: list[Node] = []
        self.node_set: dict[str, Node] = {}

        self.link_set: set[tuple[str, str]] = set()
        self.links: list[Link] = []

        self.tag_set: set[str] = set()
        self.tags: list[str] = []

        self.model_prefixs = model_prefixs

    def analysis(
            self, app: FastAPI,
            include_tags: list[str] | None = None,
            ):
        """
        1. get routes which return pydantic schema
        2. iterate routes, construct the nodes and links
        """
        schemas: list[type[BaseModel]] = []

        for route in app.routes:
            if isinstance(route, routing.APIRoute) and route.response_model:
                route_name = f'{route.endpoint.__name__}_{route.path}_{",".join(route.methods)}'.replace('/','_').lower()
                # determine route tag (first tag or fallback)
                tags = getattr(route, 'tags', None)
                route_tag = tags[0] if tags else '__default__'

                # apply filter if provided
                if include_tags and route_tag not in include_tags:
                    continue

                if route_tag not in self.tag_set:
                    self.tag_set.add(route_tag)
                    self.tags.append(route_tag)

                self.links.append(Link(
                    source=route_tag,
                    target=route_name,
                    type='entry'
                ))
                
                response_model = route.response_model
                core_schemas = get_core_types(response_model)

                for schema in core_schemas:
                    if schema and issubclass(schema, BaseModel):
                        # Record route once per schema appearance (duplicates acceptable for now?)
                        self.routes.append(Route(
                            id=route_name,
                            name=route_name,
                            tag=route_tag
                        ))
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
        is_model = any(full_name.startswith(prefix) for prefix in self.model_prefixs) if self.model_prefixs else False

        if full_name not in self.node_set:
            self.node_set[full_name] = Node(
                id=full_name, 
                name=schema.__name__,
                is_model=is_model,
                node_info=NodeInfo(
                    is_entry=False,
                    router_name="xxx",
                    fields=[]
                )
            )
        return full_name

    def add_to_link_set(self, source: str, target: str, type: Literal['child', 'parent', 'subset']):
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

        if subset_reference := getattr(schema, ENSURE_SUBSET_REFERENCE, None):
            if issubclass(subset_reference, BaseModel) and subset_reference is not BaseModel:
                self.add_to_node_set(subset_reference)
                self.add_to_link_set(full_class_name(schema), full_class_name(subset_reference), type='subset')

        # 处理所有基类的继承关系
        for base_class in schema.__bases__:
            if issubclass(base_class, BaseModel) and base_class is not BaseModel:
                self.add_to_node_set(base_class)
                self.add_to_link_set(full_class_name(schema), full_class_name(base_class), type='parent')

        for k, v in schema.model_fields.items():
            annos = get_core_types(v.annotation)
            for anno in annos:
                if anno and issubclass(anno, BaseModel):
                    self.add_to_node_set(anno)

                    if self.add_to_link_set(full_class_name(schema), full_class_name(anno), type='child'):
                        self.walk_schema(anno)


    def generate_dot(self):
        """
        """
        def _get_link_attributes(link: Link):
            """获取链接的样式和标签属性"""
            if link.type == 'child':
                return 'style = "dashed", label = "has"'
            elif link.type == 'parent':
                return 'style = "solid", label = "inherits"'
            elif link.type == 'entry':
                return 'style = "bold", label = ""'
            elif link.type == 'subset':
                return 'style = "dotted", label = "subset"'
            return 'style = "solid"'

        tags = [
            f'''
            "{t}" [
                label = "{t}"
                shape = "record"
            ];''' for t in self.tags]
        tag_str = '\n'.join(tags)

        routes = [
            f'''
            "{r.id}" [
                label = "{r.name}"
                shape = "record"
                fillcolor = "lightgreen"
                style = "filled"
            ];''' for r in self.routes]
        route_str = '\n'.join(routes)

        model_nodes = [
            f'''
            "{node.id}" [
                label = "{node.name}"
                shape = "record"
                fillcolor = "lightblue"
            ];''' for node in self.nodes if node.is_model]
        model_node_str = '\n'.join(model_nodes)

        nodes = [
            f'''
            "{node.id}" [
                label = "{node.name}"
                shape = "record"
            ];''' for node in self.nodes if node.is_model is False]
        node_str = '\n'.join(nodes)

        links = [
            f'''"{link.source}" -> "{link.target}" [ {_get_link_attributes(link)} ];''' for link in self.links
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

            {tag_str}

            subgraph cluster_A {{
                style = "rounded";
                    {route_str}
            }};

            subgraph cluster_B {{
                label = "schema"
                    {node_str}
            }}


            subgraph cluster_C {{
                label = "model"
                    {model_node_str}
            }}

            {link_str}
            }}
        '''
        return template