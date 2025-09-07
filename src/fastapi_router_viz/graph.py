from typing import Literal
from fastapi import FastAPI, routing
from fastapi_router_viz.type_helper import get_core_types, full_class_name, get_type_name
from pydantic import BaseModel
from fastapi_router_viz.type import Route, SchemaNode, Link, Tag, FieldInfo

# support pydantic-resolve's ensure_subset
ENSURE_SUBSET_REFERENCE = '__pydantic_resolve_ensure_subset_reference__'

class Analytics:
    def __init__(
            self, 
            model_prefixs: list[str] | None = None,
            schema: str | None = None):

        self.routes: list[Route] = []

        self.nodes: list[SchemaNode] = []
        self.node_set: dict[str, SchemaNode] = {}

        self.link_set: set[tuple[str, str]] = set()
        self.links: list[Link] = []

        self.tag_set: set[str] = set()
        self.tags: list[Tag] = []

        self.model_prefixs = model_prefixs
        self.schema = schema

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
                route_id = f'{route.endpoint.__name__}_{route.path}_{",".join(route.methods)}'.replace('/','_').lower()
                route_name = route.endpoint.__name__

                tags = getattr(route, 'tags', None)
                route_tag = tags[0] if tags else '__default__'

                # apply filter if provided
                if include_tags and route_tag not in include_tags:
                    continue

                tag_id=f'tag:${route_tag}'
                if route_tag not in self.tag_set:
                    self.tag_set.add(route_tag)
                    self.tags.append(Tag(
                        id=f'tag:${route_tag}',
                        name=route_tag
                    ))
                
                response_model = route.response_model
                core_schemas = get_core_types(response_model)

                for schema in core_schemas:
                    if schema and issubclass(schema, BaseModel):
                        self.links.append(Link(
                            source=tag_id,
                            target=route_id,
                            type='entry'
                        ))
                        self.routes.append(Route(
                            id=route_id,
                            name=route_name,
                        ))
                        self.links.append(Link(
                            source=route_id,
                            target=self.generate_node_head(full_class_name(schema)),
                            type='entry'
                        ))
                        schemas.append(schema)

        for s in schemas:
            self.analysis_schemas(s)
        
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
            self.node_set[full_name] = SchemaNode(
                id=full_name, 
                name=schema.__name__,
                is_model=is_model,
                fields=self.get_pydantic_fields(schema)
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

    def generate_node_head(self, link_name: str):
        return f'{link_name}::__pk__'

    def analysis_schemas(self, schema: type[BaseModel]):
        """
        1. cls is the source, add schema
        2. pydantic fields are targets, if annotation is subclass of BaseMode, add fields and add links
        3. recursively run walk_schema
        """
        self.add_to_node_set(schema)

        if subset_reference := getattr(schema, ENSURE_SUBSET_REFERENCE, None):
            if issubclass(subset_reference, BaseModel) and subset_reference is not BaseModel:
                self.add_to_node_set(subset_reference)
                self.add_to_link_set(
                    self.generate_node_head(full_class_name(schema)),
                    self.generate_node_head(full_class_name(subset_reference)), type='subset')

        # 处理所有基类的继承关系
        for base_class in schema.__bases__:
            if issubclass(base_class, BaseModel) and base_class is not BaseModel:
                self.add_to_node_set(base_class)
                self.add_to_link_set(self.generate_node_head(full_class_name(schema)),
                                     self.generate_node_head(full_class_name(base_class)), type='parent')

        for k, v in schema.model_fields.items():
            annos = get_core_types(v.annotation)
            for anno in annos:
                if anno and issubclass(anno, BaseModel):
                    self.add_to_node_set(anno)
                    if self.add_to_link_set(f'{full_class_name(schema)}::{k}',
                                            self.generate_node_head(full_class_name(anno)), type='internal'):
                        self.analysis_schemas(anno)

    def filter_nodes_and_schemas_based_on_schemas(self):
        """
        0. if self.schema is none, return original self.tags, self.routes, self.nodes, self.links
        1. search nodes based on self.schema (a str, filter self.nodes with node.name), and collect the node.id
        2. starting from these node.id, extend to the RIGHT via model links (child/parent/subset) recursively;
           extend to the LEFT only via entry links in reverse (schema <- route <- tag) for the seed schema.
        3. using the collected node.id to filter out self.tags, self.routes, self.nodes and self.links
        4. return the new tags, routes, nodes, links
        """
        if self.schema is None:
            return self.tags, self.routes, self.nodes, self.links

        seed_node_ids: set[str] = {n.id for n in self.nodes if n.name == self.schema}

        if not seed_node_ids:
            return self.tags, self.routes, self.nodes, self.links

        # 2. 根据 links 生成两个邻接 Map
        fwd: dict[str, set[str]] = {}
        rev: dict[str, set[str]] = {}
        for lk in self.links:
            fwd.setdefault(lk.source, set()).add(lk.target)
            rev.setdefault(lk.target, set()).add(lk.source)

        # 往上游：使用 rev 反向邻接，直到不再新增
        upstream: set[str] = set()
        frontier = set(seed_node_ids)
        while frontier:
            new_layer: set[str] = set()
            for nid in frontier:
                for src in rev.get(nid, ()):  # 所有指向 nid 的源
                    if src not in upstream and src not in seed_node_ids:
                        new_layer.add(src)
            upstream.update(new_layer)
            frontier = new_layer

        # 往下游：使用 fwd 正向邻接，直到不再新增
        downstream: set[str] = set()
        frontier = set(seed_node_ids)
        while frontier:
            new_layer: set[str] = set()
            for nid in frontier:
                for tgt in fwd.get(nid, ()):  # nid 指向的所有目标
                    if tgt not in downstream and tgt not in seed_node_ids:
                        new_layer.add(tgt)
            downstream.update(new_layer)
            frontier = new_layer

        included_ids: set[str] = set(seed_node_ids) | upstream | downstream

        # 3. 基于收集到的 ID 过滤各类元素
        _nodes = [n for n in self.nodes if n.id in included_ids]
        _links = [l for l in self.links if l.source in included_ids and l.target in included_ids]
        _tags = [t for t in self.tags if t.id in included_ids]
        _routes = [r for r in self.routes if r.id in included_ids]

        return _tags, _routes, _nodes, _links
    
    def get_pydantic_fields(self, schema: type[BaseModel]) -> list[FieldInfo]:
        # Convert typing annotations to concise, readable names without breaking Graphviz record labels
        # Handles Optional, Union, Annotated, generics (List/Dict/Set/Tuple), ForwardRef, builtins, Any, None
        fields = []
        for k, v in schema.model_fields.items():
            anno = v.annotation
            fields.append(FieldInfo(
                name=k,
                type_name=get_type_name(anno)
            ))
        return fields

    def generate_node_label(self, node: SchemaNode):
        name = node.name
        fields = []
        for field in node.fields:
            fields.append(f'<{field.name}> {field.name}: {field.type_name}')
        field_str = ' | '.join(fields)
        return f'<__pk__> {name} | {field_str}' if field_str else name

    def generate_dot(self):
        def _get_link_attributes(link: Link):
            """获取链接的样式和标签属性"""
            if link.type == 'child':
                return 'style = "dashed", label = ""'
            elif link.type == 'parent':
                return 'style = "solid", label = "inherits"'
            elif link.type == 'entry':
                return 'style = "bold", label = ""'
            elif link.type == 'subset':
                return 'style = "dotted", label = "subset"'
            return 'style = "solid"'

        _tags, _routes, _nodes, _links = self.filter_nodes_and_schemas_based_on_schemas()


        tags = [
            f'''
            "{t.id}" [
                label = "{t.name}"
                shape = "record"
            ];''' for t in _tags]
        tag_str = '\n'.join(tags)

        routes = [
            f'''
            "{r.id}" [
                label = "{r.name}"
                shape = "record"
                fillcolor = "lightgreen"
                style = "filled"
            ];''' for r in _routes]
        route_str = '\n'.join(routes)

        model_nodes = [
            f'''
            "{node.id}" [
                label = "{self.generate_node_label(node)}"
                shape = "record"
                fillcolor = "lightblue"
                style = "filled"
            ];''' for node in _nodes if node.is_model]
        model_node_str = '\n'.join(model_nodes)

        nodes = [
            f'''
            "{node.id}" [
                label = "{self.generate_node_label(node)}"
                shape = "record"
            ];''' for node in _nodes if node.is_model is False]
        node_str = '\n'.join(nodes)

        def handle_entry(source: str):
            if '::' in source:
                a, b = source.split('::', 1)
                return f'"{a}":{b}'
            return f'"{source}"'

        links = [
            f'''{handle_entry(link.source)} -> {handle_entry(link.target)} [ {_get_link_attributes(link)} ];''' for link in _links
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
                color = "lightgreen";
                penwidth = 3;
                    {route_str}
            }};

            subgraph cluster_B {{
                label = "schema"
                    {node_str}
            }}


            subgraph cluster_C {{
                label = "model"
                color = "lightblue";
                penwidth = 3;
                    {model_node_str}
            }}

            {link_str}
            }}
        '''
        return template