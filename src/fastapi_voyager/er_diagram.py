from __future__ import annotations

from fastapi_voyager.type_helper import (
    update_forward_refs,
    full_class_name,
    get_core_types,
    get_type_name
)
from fastapi_voyager.type import (
    FieldInfo,
    PK,
    FieldType,
    LinkType,
    Link,
    ModuleNode,
    SchemaNode,
)
from pydantic import BaseModel
from pydantic_resolve import ErDiagram, Entity, Relationship, MultipleRelationship
from logging import getLogger
from fastapi_voyager.module import build_module_schema_tree

logger = getLogger(__name__)


class DiagramRenderer:
    def __init__(
        self,
        *,
        show_fields: FieldType = 'single',
        show_module: bool = True
    ) -> None:
        self.show_fields = show_fields if show_fields in ('single', 'object', 'all') else 'single'
        self.show_module = show_module

        logger.info(f'show_module: {self.show_module}')

    def render_schema_label(self, node: SchemaNode, color: str | None=None) -> str:
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

        header_color = '#009485' if color is None else color
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
        if link.type == 'schema':
            return f"""{h(link.source)}:e -> {h(link.target)}:w [style = "{link.style}", label = "{link.label}", minlen=3];"""
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

        def render_module_schema(mod: ModuleNode, show_cluster:bool=True) -> str:
            inner_nodes = [ render_node(node) for node in mod.schema_nodes ]
            inner_nodes_str = '\n'.join(inner_nodes)
            child_str = '\n'.join(render_module_schema(mod=m, show_cluster=show_cluster) for m in mod.modules)

            if show_cluster:
                return f'''
                    subgraph cluster_module_{mod.fullname.replace('.', '_')} {{
                        tooltip="{mod.fullname}"
                        color = "#666"
                        style="rounded"
                        label = "  {mod.name}"
                        labeljust = "l"
                        pencolor="#ccc"
                        penwidth=""
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
        return '\n'.join(render_module_schema(mod=m, show_cluster=self.show_module) for m in module_schemas)

    def render_dot(self, nodes: list[SchemaNode], links: list[Link], spline_line=False) -> str:
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

            subgraph cluster_schema {{
                color = "#aaa"
                margin=18
                style="dashed"
                label="  ER Diagram"
                labeljust="l"
                fontsize="20"
                    {module_schemas_str}
            }}

            {link_str}
            }}
        '''
        return dot_str


class VoyagerErDiagram:
    def __init__(self, 
                 er_diagram: ErDiagram, 
                 show_fields: FieldType = 'single',
                 show_module: bool = False):

        self.er_diagram = er_diagram
        self.nodes: list[SchemaNode] = []
        self.node_set: dict[str, SchemaNode] = {}

        self.links: list[Link] = []
        self.link_set: set[tuple[str, str]] = set()

        self.fk_set: dict[str, set[str]] = {}

        self.show_field = show_fields
        self.show_module = show_module
    
    def generate_node_head(self, link_name: str):
        return f'{link_name}::{PK}'

    def analysis_entity(self, entity: Entity):
        schema = entity.kls
        update_forward_refs(schema)
        self.add_to_node_set(schema, fk_set=self.fk_set.get(full_class_name(schema)))

        for relationship in entity.relationships:
            annos = get_core_types(relationship.target_kls)
            for anno in annos:
                self.add_to_node_set(anno, fk_set=self.fk_set.get(full_class_name(anno)))
                source_name = f'{full_class_name(schema)}::f{relationship.field}'
                if isinstance(relationship, Relationship):
                    self.add_to_link_set(
                        source=source_name,
                        source_origin=full_class_name(schema),
                        target=self.generate_node_head(full_class_name(anno)),
                        target_origin=full_class_name(anno),
                        type='schema',
                        label=get_type_name(relationship.target_kls),
                        style='solid' if relationship.loader else 'solid, dashed'
                        )

                elif isinstance(relationship, MultipleRelationship):
                    for link in relationship.links:
                        self.add_to_link_set(
                            source=source_name,
                            source_origin=full_class_name(schema),
                            target=self.generate_node_head(full_class_name(anno)),
                            target_origin=full_class_name(anno),
                            type='schema',
                            biz=link.biz,
                            label=f'{get_type_name(relationship.target_kls)} / {link.biz} ',
                            style='solid' if link.loader else 'solid, dashed'
                        )

    def add_to_node_set(self, schema, fk_set: set[str] | None = None) -> str:
        """
        1. calc full_path, add to node_set
        2. if duplicated, do nothing, else insert
        2. return the full_path
        """
        full_name = full_class_name(schema)

        if full_name not in self.node_set:
            # skip meta info for normal queries
            self.node_set[full_name] = SchemaNode(
                id=full_name, 
                module=schema.__module__,
                name=schema.__name__,
                fields=get_fields(schema, fk_set)
            )
        return full_name

    def add_to_link_set(
            self, 
            source: str, 
            source_origin: str,
            target: str, 
            target_origin: str,
            type: LinkType,
            label: str,
            style: str,
            biz: str | None = None
        ) -> bool:
        """
        1. add link to link_set
        2. if duplicated, do nothing, else insert
        """
        pair = (source, target, biz)
        if result := pair not in self.link_set:
            self.link_set.add(pair)
            self.links.append(Link(
                source=source,
                source_origin=source_origin,
                target=target,
                target_origin=target_origin,
                type=type,
                label=label,
                style=style
            ))
        return result


    def render_dot(self):
        self.fk_set = {
            full_class_name(entity.kls): set([rel.field for rel in entity.relationships])
                for entity in self.er_diagram.configs
        }

        for entity in self.er_diagram.configs:
            self.analysis_entity(entity)
        renderer = DiagramRenderer(show_fields=self.show_field, show_module=self.show_module)
        return renderer.render_dot(list(self.node_set.values()), self.links)


def get_fields(schema: type[BaseModel], fk_set: set[str] | None = None) -> list[FieldInfo]:

    fields: list[FieldInfo] = []
    for k, v in schema.model_fields.items():
        anno = v.annotation
        fields.append(FieldInfo(
            is_object=k in fk_set if fk_set is not None else False,
            name=k,
            from_base=False,
            type_name=get_type_name(anno),
            is_exclude=bool(v.exclude)
        ))
    return fields
