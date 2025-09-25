from typing import Literal
from fastapi import FastAPI, routing
from fastapi_router_viz.type_helper import get_core_types, full_class_name, get_type_name
from pydantic import BaseModel
from fastapi_router_viz.type import Route, SchemaNode, Link, Tag, FieldInfo, ModuleNode
from fastapi_router_viz.module import build_module_tree

# support pydantic-resolve's ensure_subset
ENSURE_SUBSET_REFERENCE = '__pydantic_resolve_ensure_subset_reference__'
PK = "PK"

class Analytics:
    def __init__(
            self, 
            schema: str | None = None, 
            show_fields: Literal['single', 'object', 'all'] = 'single',
            include_tags: list[str] | None = None,
            module_color: dict[str, str] | None = None,
            route_name: str | None = None,
        ):

        self.routes: list[Route] = []

        self.nodes: list[SchemaNode] = []
        self.node_set: dict[str, SchemaNode] = {}

        self.link_set: set[tuple[str, str]] = set()
        self.links: list[Link] = []

        # store Tag by id, and also keep a list for rendering order
        self.tag_set: dict[str, Tag] = {}
        self.tags: list[Tag] = []

        self.include_tags = include_tags
        self.schema = schema
        self.show_fields = show_fields if show_fields in ('single','object','all') else 'object'
        self.module_color = module_color or {}
        self.route_name = route_name
    
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
            tag_id = f'tag__{route_tag}'
            if tag_id not in self.tag_set:
                tag_obj = Tag(id=tag_id, name=route_tag, routes=[])
                self.tag_set[tag_id] = tag_obj
                self.tags.append(tag_obj)

            # add route and create links
            route_id = f'{route.endpoint.__name__}_{route.path.replace("/", "_")}'
            route_name = route.endpoint.__name__

            # filter by route_name (route.id) if provided
            if self.route_name is not None and route_id != self.route_name:
                continue

            route_obj = Route(
                id=route_id,
                name=route_name
            )
            self.routes.append(route_obj)
            # add route into current tag
            self.tag_set[tag_id].routes.append(route_obj)
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
        bases_fields = self.get_bases_fields([s for s in schema.__bases__ if self._is_inheritance_of_BaseModel(s)])
        if full_name not in self.node_set:
            self.node_set[full_name] = SchemaNode(
                id=full_name, 
                module=schema.__module__,
                name=schema.__name__,
                fields=self.get_pydantic_fields(schema, bases_fields)
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

    def _is_inheritance_of_BaseModel(self, cls):
        return issubclass(cls, BaseModel) and cls is not BaseModel

    def analysis_schemas(self, schema: type[BaseModel]):
        """
        1. cls is the source, add schema
        2. pydantic fields are targets, if annotation is subclass of BaseMode, add fields and add links
        3. recursively run walk_schema
        """
        
        self.add_to_node_set(schema)

        # handle schema inside ensure_subset(schema)
        if subset_reference := getattr(schema, ENSURE_SUBSET_REFERENCE, None):
            if self._is_inheritance_of_BaseModel(subset_reference):

                self.add_to_node_set(subset_reference)
                self.add_to_link_set(
                    source=self.generate_node_head(full_class_name(schema)),
                    source_origin=full_class_name(schema),
                    target= self.generate_node_head(full_class_name(subset_reference)), 
                    target_origin=full_class_name(subset_reference),
                    type='subset')
                self.analysis_schemas(subset_reference)

        # handle bases
        for base_class in schema.__bases__:
            if self._is_inheritance_of_BaseModel(base_class):
                self.add_to_node_set(base_class)
                self.add_to_link_set(
                    source=self.generate_node_head(full_class_name(schema)),
                    source_origin=full_class_name(schema),
                    target=self.generate_node_head(full_class_name(base_class)),
                    target_origin=full_class_name(base_class),
                    type='parent')
                self.analysis_schemas(base_class)

        # handle fields
        for k, v in schema.model_fields.items():
            annos = get_core_types(v.annotation)
            for anno in annos:
                if anno and self._is_inheritance_of_BaseModel(anno):
                    self.add_to_node_set(anno)
                    # add f prefix to fix highlight issue in vsc graphviz interactive previewer
                    source_name = f'{full_class_name(schema)}::f{k}'
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

        # Prefer matching by fullname (node.id). If no match, fall back to simple name.
        seed_node_ids: set[str] = {n.id for n in self.nodes if n.id == self.schema}

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
    
    def _is_object(self, cls):
        _types = get_core_types(cls)
        return any(self._is_inheritance_of_BaseModel(t) for t in _types if t)

    def get_pydantic_fields(self, schema: type[BaseModel], bases_fields: set[str]) -> list[FieldInfo]:
        fields = []
        for k, v in schema.model_fields.items():
            anno = v.annotation
            fields.append(FieldInfo(
                is_object=self._is_object(anno),
                name=k,
                from_base=k in bases_fields,
                type_name=get_type_name(anno)
            ))
        return fields
    
    def get_bases_fields(self, schemas: list[type[BaseModel]]) -> set[str]:
        fields = set()
        for schema in schemas:
            for k, _ in schema.model_fields.items():
                fields.add(k)
        return fields


    def generate_node_label(self, node: SchemaNode):
        has_base_fields = any(f.from_base for f in node.fields)

        fields = [n for n in node.fields if n.from_base is False]

        name = node.name
        fields_parts: list[str] = []

        if self.show_fields == 'all':
            _fields = fields
            if has_base_fields:
                fields_parts.append('<tr><td align="left" cellpadding="8"><font color="#999">  Inherited Fields ... </font></td></tr>')
        elif self.show_fields == 'object':
            _fields = [f for f in fields if f.is_object is True]
            
        else:  # 'single'
            _fields = []

        for field in _fields:
            type_name = field.type_name[:25] + '..' if len(field.type_name) > 25 else field.type_name
            field_str = f"""<tr><td align="left" port="f{field.name}" cellpadding="8"><font>  {field.name}: {type_name}    </font></td></tr>""" 
            fields_parts.append(field_str)
        
        header_color = 'tomato' if node.id == self.schema else '#009485'
        header = f"""<tr><td cellpadding="1.5" bgcolor="{header_color}" align="center" colspan="1" port="{PK}"> <font color="white">{name}</font> </td> </tr>"""
        field_content = ''.join(fields_parts) if fields_parts else ''

        return f"""<<table border="1" cellborder="0" cellpadding="0" bgcolor="white"> {header} {field_content}   </table>>"""

    def generate_dot(self):
        def _get_link_attributes(link: Link):
            if link.type == 'child':
                return 'style = "dashed", label = "", minlen=3'
            elif link.type == 'parent':
                return 'style = "solid", dir="back", minlen=3, taillabel = "< inherit >", color = "purple", tailport="n"'
            elif link.type == 'entry':
                return 'style = "solid", label = "", minlen=3'
            elif link.type == 'subset':
                return 'style = "solid", dir="back", minlen=3, taillabel = "< subset >", color = "orange", tailport="n"'

            return 'style = "solid", arrowtail="odiamond", dir="back", minlen=3'

        _tags, _routes, _nodes, _links = self.filter_nodes_and_schemas_based_on_schemas()
        _modules = build_module_tree(_nodes)

        tags = [
            f'''
            "{t.id}" [
                label = "    {t.name}    "
                shape = "record"
            ];''' for t in _tags]
        tag_str = '\n'.join(tags)

        routes = [
            f'''
            "{r.id}" [
                label = "    {r.name}    "
                shape = "record"
            ];''' for r in _routes]
        route_str = '\n'.join(routes)

        def render_module(mod: ModuleNode):
            color = self.module_color.get(mod.fullname)
            # render schema nodes inside this module
            inner_nodes = [
                f'''
                "{node.id}" [
                    label = {self.generate_node_label(node)}
                    shape = "plain"
                ];''' for node in mod.schema_nodes
            ]
            inner_nodes_str = '\n'.join(inner_nodes)

            # render child modules recursively
            child_str = '\n'.join(render_module(m) for m in mod.modules)

            return f'''
            subgraph cluster_module_{mod.fullname.replace('.', '_')} {{
                color = "#666"
                label = "{mod.name}"
                labeljust = "l"
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
                color = "#666"
                label = "Tags"
                labeljust = "l"
                style = "rounded";
                fontsize = "20"
                {tag_str}
            }}

            subgraph cluster_router {{
                color = "#666"
                label = "Route apis"
                labeljust = "l"
                style = "rounded";
                fontsize = "20"
                {route_str}
            }}

            subgraph cluster_schema {{
                color = "#666"
                label = "Schema"
                labeljust = "l"
                fontsize = "20"
                style = "rounded";
                    {modules_str}
            }}

            {link_str}
            }}
        '''
        return template