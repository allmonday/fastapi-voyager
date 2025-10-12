from typing import Optional
from fastapi_voyager.type import SchemaNode, ModuleNode, Link, Tag, Route, FieldType, PK, ModuleRoute
from fastapi_voyager.module import build_module_schema_tree, build_module_route_tree


class Renderer:
    def __init__(
        self,
        *,
        show_fields: FieldType = 'single',
        module_color: dict[str, str] | None = None,
        schema: str | None = None,
    ) -> None:
        self.show_fields = show_fields if show_fields in ('single', 'object', 'all') else 'single'
        self.module_color = module_color or {}
        self.schema = schema

    def render_schema_label(self, node: SchemaNode) -> str:
        has_base_fields = any(f.from_base for f in node.fields)
        fields = [n for n in node.fields if n.from_base is False]

        if self.show_fields == 'all':
            _fields = fields
        elif self.show_fields == 'object':
            _fields = [f for f in fields if f.is_object is True]
        else:  # 'single'
            _fields = []

        fields_parts: list[str] = []
        if self.show_fields == 'all' and has_base_fields:
            fields_parts.append('<tr><td align="left" cellpadding="8"><font color="#999">  Inherited Fields ... </font></td></tr>')

        for field in _fields:
            type_name = field.type_name[:25] + '..' if len(field.type_name) > 25 else field.type_name
            display_xml = f'<s align="left">{field.name}: {type_name}</s>' if field.is_exclude else f'{field.name}: {type_name}'
            field_str = f"""<tr><td align="left" port="f{field.name}" cellpadding="8"><font>  {display_xml}    </font></td></tr>"""
            fields_parts.append(field_str)

        header_color = 'tomato' if node.id == self.schema else '#009485'
        header = f"""<tr><td cellpadding="1.5" bgcolor="{header_color}" align="center" colspan="1" port="{PK}"> <font color="white">    {node.name}    </font> </td> </tr>"""
        field_content = ''.join(fields_parts) if fields_parts else ''
        return f"""<<table border="1" cellborder="0" cellpadding="0" bgcolor="white"> {header} {field_content}   </table>>"""

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
        else:
            raise ValueError(f'Unknown link type: {link.type}')

    def render_module_schema_wrapper(self, mods: list[ModuleNode]) -> str:
        module_color_flag = set(self.module_color.keys())
        print(module_color_flag)

        def render_module_schema(mod: ModuleNode) -> str:
            color: Optional[str] = None

            for k in module_color_flag:
                if mod.fullname.startswith(k):
                    module_color_flag.remove(k)
                    color = self.module_color[k]
                    break

            inner_nodes = [
                f'''
                    "{node.id}" [
                        label = {self.render_schema_label(node)}
                        shape = "plain"
                        margin="0.5,0.1"
                    ];''' for node in mod.schema_nodes
            ]
            inner_nodes_str = '\n'.join(inner_nodes)
            child_str = '\n'.join(render_module_schema(m) for m in mod.modules)
            return f'''
                subgraph cluster_module_{mod.fullname.replace('.', '_')} {{
                    tooltip="{mod.fullname}"
                    color = "#666"
                    style="rounded"
                    label = "  {mod.name}"
                    labeljust = "l"
                    {(f'pencolor = "{color}"' if color else 'pencolor="#ccc"')}
                    {(f'penwidth = 3' if color else 'penwidth=""')}
                    {inner_nodes_str}
                    {child_str}
                }}'''
        return '\n'.join(render_module_schema(m) for m in mods)
    
    def render_module_route(self, mod: ModuleRoute) -> str:
        # Inner route nodes, same style as flat route_str
        inner_nodes = [
            f'''
            "{r.id}" [
                label = "    {r.name}    "
                margin="0.5,0.1"
                shape = "record"
            ];''' for r in mod.routes
        ]
        inner_nodes_str = '\n'.join(inner_nodes)
        child_str = '\n'.join(self.render_module_route(m) for m in mod.modules)
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

    def render_dot(self, tags: list[Tag], routes: list[Route], nodes: list[SchemaNode], links: list[Link]) -> str:
        module_schemas = build_module_schema_tree(nodes)
        module_routes = build_module_route_tree(routes)

        tag_str = '\n'.join([
            f'''
            "{t.id}" [
                label = "    {t.name}    "
                shape = "record"
                margin="0.5,0.1"
            ];''' for t in tags
        ])


        module_schemas_str = self.render_module_schema_wrapper(module_schemas)
        module_routes_str = '\n'.join(self.render_module_route(m) for m in module_routes)
        link_str = '\n'.join(self.render_link(link) for link in links)

        dot_str = f'''
        digraph world {{
            pad="0.5"
            nodesep=0.8
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