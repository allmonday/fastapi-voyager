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
from fastapi_voyager.render import Renderer
from fastapi_voyager.render_style import RenderConfig
from pydantic import BaseModel
from pydantic_resolve import ErDiagram, Entity, Relationship, MultipleRelationship
from logging import getLogger

logger = getLogger(__name__)


class DiagramRenderer(Renderer):
    """
    Renderer for Entity-Relationship diagrams.

    Inherits from Renderer to reuse template system and styling.
    ER diagrams have simpler structure (no tags/routes), so we only
    need to customize the top-level DOT structure.
    """

    def __init__(
        self,
        *,
        show_fields: FieldType = 'single',
        show_module: bool = True
    ) -> None:
        # Initialize parent Renderer with shared config
        super().__init__(
            show_fields=show_fields,
            show_module=show_module,
            config=RenderConfig()  # Use unified style configuration
        )
        logger.info(f'show_module: {self.show_module}')

    def render_link(self, link: Link) -> str:
        """Override to increase link length by 40% for ER diagrams."""
        source = self._handle_schema_anchor(link.source)
        target = self._handle_schema_anchor(link.target)

        # Build link attributes
        if link.style is not None:
            attrs = {'style': link.style}
            if link.label:
                attrs['label'] = link.label
            # Increase minlen by 40% (3 * 1.4 = 4.2, round to 4)
            attrs['minlen'] = 4
        else:
            attrs = self.style.get_link_attributes(link.type)
            if link.label:
                attrs['label'] = link.label

        return self.template_renderer.render_template(
            'dot/link.j2',
            source=source,
            target=target,
            attributes=self._format_link_attributes(attrs)
        )

    def render_dot(self, nodes: list[SchemaNode], links: list[Link], spline_line=False) -> str:
        """
        Render ER diagram as DOT format.

        Reuses parent's render_module_schema_content and render_link methods.
        Only customizes the top-level digraph structure.
        """
        # Reuse parent's module schema rendering
        module_schemas_str = self.render_module_schema_content(nodes)

        # Reuse parent's link rendering
        link_str = '\n'.join(self.render_link(link) for link in links)

        # Render using ER diagram template
        return self.template_renderer.render_template(
            'dot/er_diagram.j2',
            pad=self.style.pad,
            nodesep=self.style.nodesep,
            font=self.style.font,
            node_fontsize=self.style.node_fontsize,
            spline='line' if spline_line else None,
            er_cluster=module_schemas_str,
            links=link_str
        )


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
