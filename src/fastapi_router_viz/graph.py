import inspect
from typing import Literal
from fastapi import FastAPI, routing
from fastapi_router_viz.type_helper import (
    get_core_types,
    full_class_name,
    get_bases_fields,
    is_inheritance_of_pydantic_base,
    get_pydantic_fields,
    get_vscode_link,
    get_source
)
from pydantic import BaseModel
from fastapi_router_viz.type import Route, SchemaNode, Link, Tag, ModuleNode
from fastapi_router_viz.module import build_module_tree
from fastapi_router_viz.filter import filter_graph

# support pydantic-resolve's ensure_subset
ENSURE_SUBSET_REFERENCE = '__pydantic_resolve_ensure_subset_reference__'
PK = "PK"

class Analytics:
    def __init__(
            self, 
            schema: str | None = None, 
            schema_field: str | None = None,
            show_fields: Literal['single', 'object', 'all'] = 'single',
            include_tags: list[str] | None = None,
            module_color: dict[str, str] | None = None,
            route_name: str | None = None,
            load_meta: bool = False
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
        self.schema_field = schema_field
        self.show_fields = show_fields if show_fields in ('single','object','all') else 'object'
        self.module_color = module_color or {}
        self.route_name = route_name
        self.load_meta = load_meta
    

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
                name=route_name,
                source_code=inspect.getsource(route.endpoint)
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
        bases_fields = get_bases_fields([s for s in schema.__bases__ if is_inheritance_of_pydantic_base(s)])
        if full_name not in self.node_set:
            # skip meta info for normal queries
            self.node_set[full_name] = SchemaNode(
                id=full_name, 
                module=schema.__module__,
                name=schema.__name__,
                source_code=get_source(schema) if self.load_meta else None,
                vscode_link=get_vscode_link(schema) if self.load_meta else None,
                fields=get_pydantic_fields(schema, bases_fields)
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


    def analysis_schemas(self, schema: type[BaseModel]):
        """
        1. cls is the source, add schema
        2. pydantic fields are targets, if annotation is subclass of BaseMode, add fields and add links
        3. recursively run walk_schema
        """
        
        self.add_to_node_set(schema)

        # handle schema inside ensure_subset(schema)
        if subset_reference := getattr(schema, ENSURE_SUBSET_REFERENCE, None):
            if is_inheritance_of_pydantic_base(subset_reference):

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
            if is_inheritance_of_pydantic_base(base_class):
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
                if anno and is_inheritance_of_pydantic_base(anno):
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


    def generate_node_head(self, link_name: str):
        return f'{link_name}::{PK}'


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
            display_xml = f'<s align="left">{field.name}: {type_name}</s>' if field.is_exclude else f'{field.name}: {type_name}'
            field_str = f"""<tr><td align="left" port="f{field.name}" cellpadding="8"><font>  {display_xml}    </font></td></tr>""" 
            fields_parts.append(field_str)
        
        header_color = 'tomato' if node.id == self.schema else '#009485'
        header = f"""<tr><td cellpadding="1.5" bgcolor="{header_color}" align="center" colspan="1" port="{PK}"> <font color="white">    {name}    </font> </td> </tr>"""
        field_content = ''.join(fields_parts) if fields_parts else ''

        return f"""<<table border="1" cellborder="0" cellpadding="0" bgcolor="white"> {header} {field_content}   </table>>"""

    def generate_dot(self):

        def get_link_attributes(link: Link):
            if link.type == 'child':
                return 'style = "dashed", label = "", minlen=3'
            elif link.type == 'parent':
                return 'style = "solid", dir="back", minlen=3, taillabel = "< inherit >", color = "purple", tailport="n"'
            elif link.type == 'entry':
                return 'style = "solid", label = "", minlen=3'
            elif link.type == 'subset':
                return 'style = "solid", dir="back", minlen=3, taillabel = "< subset >", color = "orange", tailport="n"'

            return 'style = "solid", arrowtail="odiamond", dir="back", minlen=3'

        def render_module(mod: ModuleNode):
            color = self.module_color.get(mod.fullname)
            # render schema nodes inside this module
            inner_nodes = [
                f'''
                "{node.id}" [
                    label = {self.generate_node_label(node)}
                    shape = "plain"
                    margin="0.5,0.1"
                ];''' for node in mod.schema_nodes
            ]
            inner_nodes_str = '\n'.join(inner_nodes)

            # render child modules recursively
            child_str = '\n'.join(render_module(m) for m in mod.modules)

            return f'''
            subgraph cluster_module_{mod.fullname.replace('.', '_')} {{
                color = "#666"
                style="rounded"
                label = "  {mod.name}"
                labeljust = "l"
                {(f'pencolor = "{color}"' if color else 'pencolor=""')}
                {(f'penwidth = 3' if color else 'penwidth=""')}
                {inner_nodes_str}
                {child_str}
            }}'''

        def handle_entry(source: str):
            if '::' in source:
                a, b = source.split('::', 1)
                return f'"{a}":{b}'
            return f'"{source}"'


        _tags, _routes, _nodes, _links = filter_graph(
            schema=self.schema,
            schema_field=self.schema_field,
            tags=self.tags,
            routes=self.routes,
            nodes=self.nodes,
            links=self.links,
            node_set=self.node_set,
        )
        _modules = build_module_tree(_nodes)

        tags = [
            f'''
            "{t.id}" [
                label = "    {t.name}    "
                shape = "record"
                margin="0.5,0.1"
            ];''' for t in _tags]
        tag_str = '\n'.join(tags)

        routes = [
            f'''
            "{r.id}" [
                label = "    {r.name}    "
                margin="0.5,0.1"
                shape = "record"
            ];''' for r in _routes]
        route_str = '\n'.join(routes)

        modules_str = '\n'.join(render_module(m) for m in _modules)

        links = [
            f'''{handle_entry(link.source)} -> {handle_entry(link.target)} [ {get_link_attributes(link)} ];''' for link in _links
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
                color = "#aaa"
                margin=18
                style="dashed"
                label = "  Tags"
                labeljust = "l"
                fontsize = "20"
                {tag_str}
            }}

            subgraph cluster_router {{
                color = "#aaa"
                margin=18
                style="dashed"
                label = "  Route apis"
                labeljust = "l"
                fontsize = "20"
                {route_str}
            }}

            subgraph cluster_schema {{
                color = "#aaa"
                margin=18
                style="dashed"
                label="  Schema"
                labeljust="l"
                fontsize="20"
                    {modules_str}
            }}

            {link_str}
            }}
        '''
        return template