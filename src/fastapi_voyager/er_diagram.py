from __future__ import annotations

from fastapi_voyager.type import PK, CoreData, FieldType, Link, LinkType, Route, SchemaNode, Tag
from fastapi_voyager.type_helper import (
    update_forward_refs,
    full_class_name,
    get_pydantic_fields,
    get_core_types,
)
from fastapi_voyager.render import Renderer

from pydantic_resolve import ErDiagram, Entity
import pydantic_resolve.constant as const

class VoyagerErDiagram:
    def __init__(self, er_diagram: ErDiagram):
        self.er_diagram = er_diagram
        self.nodes: list[SchemaNode] = []
        self.node_set: dict[str, SchemaNode] = {}

        self.links: list[Link] = []
        self.link_set: set[tuple[str, str]] = set()
    
    def generate_node_head(self, link_name: str):
        return f'{link_name}::{PK}'

    def analysis_entity(self, entity: Entity):
        schema = entity.kls
        update_forward_refs(schema)
        self.add_to_node_set(schema)

        for relationship in entity.relationships:
            annos = get_core_types(relationship.target_kls)
            print(annos)
            for anno in annos:
                self.add_to_node_set(anno)
                source_name = f'{full_class_name(schema)}::f{relationship.field}'
                self.add_to_link_set(
                    source=source_name,
                    source_origin=full_class_name(schema),
                    target=self.generate_node_head(full_class_name(anno)),
                    target_origin=full_class_name(anno),
                    type='schema')

    def add_to_node_set(self, schema):
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
                fields=get_pydantic_fields(schema, set())
            )
        return full_name

    def add_to_link_set(
            self, 
            source: str, 
            source_origin: str,
            target: str, 
            target_origin: str,
            type: LinkType
        ) -> bool:
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


    def render_dot(self):
        for entity in self.er_diagram.configs:
            self.analysis_entity(entity)
        print(self.node_set)
        renderer = Renderer(show_fields='all')
        return renderer.render_dot([], [], list(self.node_set.values()), self.links)