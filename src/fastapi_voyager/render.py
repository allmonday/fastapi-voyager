from logging import getLogger

from fastapi_voyager.module import build_module_route_tree, build_module_schema_tree
from fastapi_voyager.type import (
    PK,
    FieldType,
    Link,
    FieldInfo,
    ModuleNode,
    ModuleRoute,
    Route,
    SchemaNode,
    Tag,
)

logger = getLogger(__name__)


class Renderer:
    def __init__(
        self,
        *,
        show_fields: FieldType = 'single',
        module_color: dict[str, str] | None = None,
        schema: str | None = None,
        show_module: bool = True,
        show_pydantic_resolve_meta: bool = False,
    ) -> None:
        self.show_fields = show_fields if show_fields in ('single', 'object', 'all') else 'single'
        self.module_color = module_color or {}
        self.schema = schema
        self.show_module = show_module
        self.show_pydantic_resolve_meta = show_pydantic_resolve_meta

        logger.info(f'show_module: {self.show_module}')
        logger.info(f'module_color: {self.module_color}')
    
    def render_pydantic_related_markup(self, field: FieldInfo):
        if self.show_pydantic_resolve_meta is False:
            return ''

        parts: list[str] = []
        if field.is_resolve:
            parts.append('<font color="#47a80f">  ● resolve</font>')
        if field.is_post:
            parts.append('<font color="#427fa4">  ● post</font>')
        if field.expose_as_info:
            parts.append(f'<font color="#895cb9">  ● expose as: {field.expose_as_info}</font>')
        if field.send_to_info:
            to_collectors = ', '.join(field.send_to_info)
            parts.append(f'<font color="#ca6d6d">  ● send to: {to_collectors}</font>')
        if field.collect_info:
            defined_collectors = ', '.join(field.collect_info)
            parts.append(f'<font color="#777">  ● collectors: {defined_collectors}</font>')

        if not parts:
            return ''
        
        return '<br align="left"/><br align="left"/>' + '<br align="left"/>'.join(parts) + '<br align="left"/>'

    def render_schema_label(self, node: SchemaNode, color: str | None=None) -> str:
        """
        TODO: should improve the logic with show_pydantic_resolve_meta
        """

        has_base_fields = any(f.from_base for f in node.fields)

        # if self.show_pydantic_resolve_meta, show all fields with resolve/post/expose/collector info
        if self.show_pydantic_resolve_meta:
            fields = [n for n in node.fields if n.has_pydantic_resolve_meta is True or n.from_base is False]
        else:
            fields = [n for n in node.fields if n.from_base is False]

        if self.show_fields == 'all':
            _fields = fields
        elif self.show_fields == 'object':
            if self.show_pydantic_resolve_meta:
                # to better display resolve meta info
                _fields = [f for f in fields if f.is_object is True or f.has_pydantic_resolve_meta is True]
            else:
                _fields = [f for f in fields if f.is_object is True]
        else:  # 'single'
            _fields = []

        fields_parts: list[str] = []
        if self.show_fields == 'all' and has_base_fields:
            fields_parts.append('<tr><td align="left" cellpadding="8"><font color="#999">  Inherited Fields ... </font></td></tr>')

        for field in _fields:
            type_name = field.type_name[:25] + '..' if len(field.type_name) > 25 else field.type_name
            display_xml = f'<s align="left">{field.name}: {type_name} </s>' if field.is_exclude else f'{field.name}: {type_name}'
            field_str = f"""<tr><td align="left" port="f{field.name}" cellpadding="8"><font>  {display_xml}  </font> {self.render_pydantic_related_markup(field)}  </td></tr>"""
            fields_parts.append(field_str)

        default_color = '#009485' if color is None else color
        header_color = 'tomato' if node.id == self.schema else default_color
        header = f"""<tr><td cellpadding="6" bgcolor="{header_color}" align="center" colspan="1" port="{PK}"> <font color="white">    {node.name}    </font></td> </tr>"""
        field_content = ''.join(fields_parts) if fields_parts else ''
        return f"""<<table border="0" cellborder="1" cellpadding="0" cellspacing="0" bgcolor="white"> {header} {field_content}   </table>>"""

    def _handle_schema_anchor(self, source: str) -> str:
        if '::' in source:
            a, b = source.split('::', 1)
            return f'"{a}":{b}'
        return f'"{source}"'

    def render_link(self, link: Link) -> str:
        h = self._handle_schema_anchor
        if link.type == 'tag_route':
            return f"""{h(link.source)}:e -> {h(link.target)}:w [style = "solid", minlen=3];"""
        elif link.type == 'route_to_schema':
            return f"""{h(link.source)}:e -> {h(link.target)}:w [style = "solid", dir="back", arrowtail="odot", minlen=3];"""
        elif link.type == 'schema':
            return f"""{h(link.source)}:e -> {h(link.target)}:w [style = "solid", label = "", dir="back", minlen=3, arrowtail="odot"];"""
        elif link.type == 'parent':
            return f"""{h(link.source)}:e -> {h(link.target)}:w [style = "solid, dashed", dir="back", minlen=3, taillabel = "< inherit >", color = "purple", tailport="n"];"""
        elif link.type == 'subset':
            return f"""{h(link.source)}:e -> {h(link.target)}:w [style = "solid, dashed", dir="back", minlen=3, taillabel = "< subset >", color = "orange", tailport="n"];"""
        elif link.type == 'tag_to_schema':
            return f"""{h(link.source)}:e -> {h(link.target)}:w [style = "solid", minlen=3];"""
        else:
            raise ValueError(f'Unknown link type: {link.type}')

    def render_module_schema_content(self, nodes: list[SchemaNode]) -> str:
        def render_node(node: SchemaNode, color: str | None=None) -> str:
            return f'''
                "{node.id}" [
                    label = {self.render_schema_label(node, color)}
                    shape = "plain"
                    margin="0.5,0.1"
                ];'''

        def render_module_schema(mod: ModuleNode, inherit_color: str | None=None, show_cluster:bool=True) -> str:
            color: str | None = inherit_color
            cluster_color: str | None = None


            # recursively vist module from short to long:  'a', 'a.b', 'a.b.c'
            # color_flag: {'a', 'a.b.c'}
            # at first 'a', match 'a' -> color, remove 'a' from color_flag
            # at 'a.b', no match
            # at 'a.b.c', match 'a.b.c' -> color, remove 'a.b.c' from color_flag
            for k in module_color_flag:
                if mod.fullname.startswith(k):  
                    module_color_flag.remove(k)
                    color = self.module_color[k]
                    cluster_color = color if color != inherit_color else None
                    break

            inner_nodes = [ render_node(node, color) for node in mod.schema_nodes ]
            inner_nodes_str = '\n'.join(inner_nodes)
            child_str = '\n'.join(render_module_schema(mod=m, inherit_color=color, show_cluster=show_cluster) for m in mod.modules)

            if show_cluster:
                return f'''
                    subgraph cluster_module_{mod.fullname.replace('.', '_')} {{
                        tooltip="{mod.fullname}"
                        color = "#666"
                        style="rounded"
                        label = "  {mod.name}"
                        labeljust = "l"
                        {(f'pencolor = "{cluster_color}"' if cluster_color else 'pencolor="#ccc"')}
                        {('penwidth = 3' if color else 'penwidth=""')}
                        {inner_nodes_str}
                        {child_str}
                    }}'''
            else:
                return f'''
                    {inner_nodes_str}
                    {child_str}
                '''

        # if self.show_module:
        module_schemas = build_module_schema_tree(nodes)
        module_color_flag = set(self.module_color.keys())
        return '\n'.join(render_module_schema(mod=m, show_cluster=self.show_module) for m in module_schemas)

    
    def render_module_route_content(self, routes: list[Route]) -> str:
        def render_route(route: Route) -> str:
            response_schema = route.response_schema[:25] + '..' if len(route.response_schema) > 25 else route.response_schema
            return f'''
                "{route.id}" [
                    label = "    {route.name} | {response_schema}    "
                    margin="0.5,0.1"
                    shape = "record"
                ];'''

        def render_module_route(mod: ModuleRoute, show_cluster: bool=True) -> str:
            # Inner route nodes, same style as flat route_str
            inner_nodes = [
                render_route(r) for r in mod.routes
            ]
            inner_nodes_str = '\n'.join(inner_nodes)
            child_str = '\n'.join(render_module_route(m, show_cluster=show_cluster) for m in mod.modules)
            if show_cluster:
                return f'''
                    subgraph cluster_route_module_{mod.fullname.replace('.', '_')} {{
                        tooltip="{mod.fullname}"
                        color = "#666"
                        style="rounded"
                        label = "  {mod.name}"
                        labeljust = "l"
                        {inner_nodes_str}
                        {child_str}
                    }}'''
            else:
                return f'''
                    {inner_nodes_str}
                    {child_str}
                '''
        module_routes = build_module_route_tree(routes)
        module_routes_str = '\n'.join(render_module_route(m, show_cluster=self.show_module) for m in module_routes)
        return module_routes_str


    def render_dot(self, tags: list[Tag], routes: list[Route], nodes: list[SchemaNode], links: list[Link], spline_line=False) -> str:

        tag_str = '\n'.join([
            f'''
            "{t.id}" [
                label = "    {t.name}    "
                shape = "record"
                margin="0.5,0.1"
            ];''' for t in tags
        ])

        module_routes_str = self.render_module_route_content(routes)
        module_schemas_str = self.render_module_schema_content(nodes)
        link_str = '\n'.join(self.render_link(link) for link in links)

        dot_str = f'''
        digraph world {{
            pad="0.5"
            nodesep=0.8
            {'splines=line' if spline_line else ''}
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
                label = "  Routes"
                labeljust = "l"
                fontsize = "20"
                {module_routes_str}
            }}

            subgraph cluster_schema {{
                color = "#aaa"
                margin=18
                style="dashed"
                label="  Schema"
                labeljust="l"
                fontsize="20"
                    {module_schemas_str}
            }}

            {link_str}
            }}
        '''
        return dot_str