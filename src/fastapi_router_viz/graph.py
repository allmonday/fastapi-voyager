from typing import Literal
from fastapi import FastAPI, routing
from fastapi_router_viz.type_helper import get_core_types, full_class_name, get_type_name
from pydantic import BaseModel
from fastapi_router_viz.type import Route, SchemaNode, Link, Tag, FieldInfo
from fastapi_router_viz.module import build_module_tree

# support pydantic-resolve's ensure_subset
ENSURE_SUBSET_REFERENCE = '__pydantic_resolve_ensure_subset_reference__'
PK = "PK"

class Analytics:
    def __init__(
            self, 
            schema: str | None = None, 
            show_fields: bool = False,
            include_tags: list[str] | None = None,
            module_color: dict[str, str] | None = None,
        ):

        self.routes: list[Route] = []

        self.nodes: list[SchemaNode] = []
        self.node_set: dict[str, SchemaNode] = {}

        self.link_set: set[tuple[str, str]] = set()
        self.links: list[Link] = []

        self.tag_set: set[str] = set()
        self.tags: list[Tag] = []

        self.include_tags = include_tags
        self.schema = schema
        self.show_fields = show_fields
        self.module_color = module_color or {}
    
    def _get_available_route(self, app: FastAPI):
        for route in app.routes:
            if isinstance(route, routing.APIRoute) and route.response_model:
                yield route


    def analysis(self, app: FastAPI):
        """
        1. get routes which return pydantic schema
            1.1 collect tags and routes, add links tag-> route
            1.2 collect response_model and links route -> response_model

        2. iterate schemas, construct the schema/model nodes and their links
        """
        schemas: list[type[BaseModel]] = []

        for route in self._get_available_route(app):
            # check tags
            tags = getattr(route, 'tags', None)
            route_tag = tags[0] if tags else '__default__'
            if self.include_tags and route_tag not in self.include_tags:
                continue

            # add tag if not exists
            tag_id=f'tag__{route_tag}'
            if route_tag not in self.tag_set:  # prevent duplication
                self.tag_set.add(route_tag)
                self.tags.append(Tag(
                    id=f'tag__{route_tag}',
                    name=route_tag))

            # add route and create links
            route_id = f'{route.endpoint.__name__}_{route.path.replace("/", "_")}'
            route_name = route.endpoint.__name__
            self.routes.append(Route(
                id=route_id,
                name=route_name))
            self.links.append(Link(
                source=tag_id,
                source_origin=tag_id,
                target=route_id,
                target_origin=route_id,
                type='entry'
            ))

            # add response_models and create links from route -> response_model
            for schema in get_core_types(route.response_model):
                if schema and issubclass(schema, BaseModel):
                    target_name = full_class_name(schema)
                    self.links.append(Link(
                        source=route_id,
                        source_origin=route_id,
                        target=self.generate_node_head(target_name),
                        target_origin=target_name,
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
        if full_name not in self.node_set:
            self.node_set[full_name] = SchemaNode(
                id=full_name, 
                module=schema.__module__,
                name=schema.__name__,
                fields=self.get_pydantic_fields(schema)
            )
        return full_name

    def add_to_link_set(
            self, 
            source: str, 
            source_origin: str,
            target: str, 
            target_origin: str,
            type: Literal['child', 'parent', 'subset']):
        """
        1. add link to link_set
        2. if duplicated, do nothing, else insert
        """
        pair = (source, target)
        if result := pair not in self.link_set:
            self.link_set.add(pair)
            self.links.append(Link(
                source=source,
                source_origin=source_origin,
                target=target,
                target_origin=target_origin,
                type=type
            ))
        return result

    def generate_node_head(self, link_name: str):
        return f'{link_name}::{PK}'

    def analysis_schemas(self, schema: type[BaseModel]):
        """
        1. cls is the source, add schema
        2. pydantic fields are targets, if annotation is subclass of BaseMode, add fields and add links
        3. recursively run walk_schema
        """
        def _is_inheritance_of_BaseModel(cls):
            return issubclass(cls, BaseModel) and cls is not BaseModel
        
        self.add_to_node_set(schema)

        # handle schema inside ensure_subset(schema)
        if subset_reference := getattr(schema, ENSURE_SUBSET_REFERENCE, None):
            if _is_inheritance_of_BaseModel(subset_reference):

                self.add_to_node_set(subset_reference)
                self.add_to_link_set(
                    source=self.generate_node_head(full_class_name(schema)),
                    source_origin=full_class_name(schema),
                    target= self.generate_node_head(full_class_name(subset_reference)), 
                    target_origin=full_class_name(subset_reference),
                    type='subset')

        # handle bases
        for base_class in schema.__bases__:
            if _is_inheritance_of_BaseModel(base_class):
                self.add_to_node_set(base_class)
                self.add_to_link_set(
                    source=self.generate_node_head(full_class_name(schema)),
                    source_origin=full_class_name(schema),
                    target=self.generate_node_head(full_class_name(base_class)),
                    target_origin=full_class_name(base_class),
                    type='parent')

        # handle fields
        for k, v in schema.model_fields.items():
            annos = get_core_types(v.annotation)
            for anno in annos:
                if anno and issubclass(anno, BaseModel):
                    self.add_to_node_set(anno)
                    # add f prefix to fix highlight issue in vsc graphviz interactive previewer
                    source_name = f'{full_class_name(schema)}::f{k}' if self.show_fields else self.generate_node_head(full_class_name(schema))
                    if self.add_to_link_set(
                        source=source_name,
                        source_origin=full_class_name(schema),
                        target=self.generate_node_head(full_class_name(anno)),
                        target_origin=full_class_name(anno),
                        type='internal'):
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

        fwd: dict[str, set[str]] = {}
        rev: dict[str, set[str]] = {}
        
        for lk in self.links:
            fwd.setdefault(lk.source_origin, set()).add(lk.target_origin)
            rev.setdefault(lk.target_origin, set()).add(lk.source_origin)

        upstream: set[str] = set()
        frontier = set(seed_node_ids)
        while frontier:
            new_layer: set[str] = set()
            for nid in frontier:
                for src in rev.get(nid, ()):
                    if src not in upstream and src not in seed_node_ids:
                        new_layer.add(src)
            upstream.update(new_layer)
            frontier = new_layer

        downstream: set[str] = set()
        frontier = set(seed_node_ids)
        while frontier:
            new_layer: set[str] = set()
            for nid in frontier:
                for tgt in fwd.get(nid, ()):
                    if tgt not in downstream and tgt not in seed_node_ids:
                        new_layer.add(tgt)
            downstream.update(new_layer)
            frontier = new_layer

        included_ids: set[str] = set(seed_node_ids) | upstream | downstream

        _nodes = [n for n in self.nodes if n.id in included_ids]
        _links = [l for l in self.links if l.source_origin in included_ids and l.target_origin in included_ids]
        _tags = [t for t in self.tags if t.id in included_ids]
        _routes = [r for r in self.routes if r.id in included_ids]

        return _tags, _routes, _nodes, _links
    
    def get_pydantic_fields(self, schema: type[BaseModel]) -> list[FieldInfo]:
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
        if self.show_fields:
            fields = []
            for field in node.fields:
                fields.append(f'<f{field.name}> {field.name}: {field.type_name}')
            field_str = ' | '.join(fields)
            return f'<{PK}> {name} | {field_str}' if field_str else name
        else:
            return f'<PK> {name}'

    def generate_dot(self):
        def _get_link_attributes(link: Link):
            if link.type == 'child':
                return 'style = "dashed", label = ""'
            elif link.type == 'parent':
                return 'style = "solid", label = "inherits", color = "purple"'
            elif link.type == 'entry':
                return 'style = "solid", label = ""'
            elif link.type == 'subset':
                return 'style = "solid", label = "subset", color = "orange"'
            return 'style = "solid"'

        _tags, _routes, _nodes, _links = self.filter_nodes_and_schemas_based_on_schemas()
        _modules = build_module_tree(_nodes)

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
            ];''' for r in _routes]
        route_str = '\n'.join(routes)

        def render_module(mod):
            color = self.module_color.get(mod.fullname)
            # render schema nodes inside this module
            inner_nodes = [
                f'''
                "{node.id}" [
                    label = "{self.generate_node_label(node)}"
                    shape = "record"
                    {(f'color = "{color}"' if color else '')}
                    {(f'fillcolor = "tomato"' if node.name == self.schema else '')}
                    {(f'style = "filled"' if node.name == self.schema else '')}
                ];''' for node in mod.schema_nodes
            ]
            inner_nodes_str = '\n'.join(inner_nodes)

            # render child modules recursively
            child_str = '\n'.join(render_module(m) for m in mod.modules)

            return f'''
            subgraph cluster_module_{mod.fullname.replace('.', '_')} {{
                label = "{mod.name}"
                {(f'color = "{color}"' if color else '')}
                {inner_nodes_str}
                {child_str}
            }}'''

        modules_str = '\n'.join(render_module(m) for m in _modules)

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
        digraph world {{
            pad="0.5"
            fontname="Helvetica,Arial,sans-serif"
            node [fontname="Helvetica,Arial,sans-serif"]
            edge [
                fontname="Helvetica,Arial,sans-serif"
                color="gray"
            ]
            graph [
                rankdir = "LR"
            ];
            node [
                fontsize = "16"
            ];

            subgraph cluster_tags {{ 
                label = "Tags"
                style = "rounded";
                fontsize = "20"
                {tag_str}
            }}

            subgraph cluster_router {{
                label = "Route apis"
                style = "rounded";
                fontsize = "20"
                {route_str}
            }}

            subgraph cluster_schema {{
                label = "Schema"
                fontsize = "20"
                style = "rounded";
                    {modules_str}
            }}

            {link_str}
            }}
        '''
        return template