"""
Render FastAPI application structure to DOT format using Jinja2 templates.
"""
from logging import getLogger
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from fastapi_voyager.module import build_module_route_tree, build_module_schema_tree
from fastapi_voyager.render_style import RenderConfig
from fastapi_voyager.type import (
    PK,
    FieldType,
    FieldInfo,
    Link,
    ModuleNode,
    ModuleRoute,
    Route,
    SchemaNode,
    Tag,
)

logger = getLogger(__name__)

# Get the template directory relative to this file
TEMPLATE_DIR = Path(__file__).parent / "templates"


class TemplateRenderer:
    """
    Jinja2-based template renderer for DOT and HTML templates.
    """

    def __init__(self, template_dir: Path = TEMPLATE_DIR):
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_template(self, template_name: str, **context) -> str:
        """Render a template with the given context."""
        template = self.env.get_template(template_name)
        return template.render(**context)


class Renderer:
    """
    Render FastAPI application structure to DOT format.

    This class handles the conversion of tags, routes, schemas, and links
    into Graphviz DOT format, with support for custom styling and filtering.
    """

    def __init__(
        self,
        *,
        show_fields: FieldType = 'single',
        module_color: dict[str, str] | None = None,
        schema: str | None = None,
        show_module: bool = True,
        show_pydantic_resolve_meta: bool = False,
        config: RenderConfig | None = None,
    ) -> None:
        self.show_fields = show_fields if show_fields in ('single', 'object', 'all') else 'single'
        self.module_color = module_color or {}
        self.schema = schema
        self.show_module = show_module
        self.show_pydantic_resolve_meta = show_pydantic_resolve_meta

        # Use provided config or create default
        self.config = config or RenderConfig()
        self.colors = self.config.colors
        self.style = self.config.style

        # Initialize template renderer
        self.template_renderer = TemplateRenderer()

        logger.info(f'show_module: {self.show_module}')
        logger.info(f'module_color: {self.module_color}')

    def _render_pydantic_meta_parts(self, field: FieldInfo) -> list[str]:
        """Render pydantic-resolve metadata as HTML parts."""
        if not self.show_pydantic_resolve_meta:
            return []

        parts = []
        if field.is_resolve:
            parts.append(
                self.template_renderer.render_template(
                    'html/colored_text.j2',
                    text='● resolve',
                    color=self.colors.resolve
                )
            )
        if field.is_post:
            parts.append(
                self.template_renderer.render_template(
                    'html/colored_text.j2',
                    text='● post',
                    color=self.colors.post
                )
            )
        if field.expose_as_info:
            parts.append(
                self.template_renderer.render_template(
                    'html/colored_text.j2',
                    text=f'● expose as: {field.expose_as_info}',
                    color=self.colors.expose_as
                )
            )
        if field.send_to_info:
            to_collectors = ', '.join(field.send_to_info)
            parts.append(
                self.template_renderer.render_template(
                    'html/colored_text.j2',
                    text=f'● send to: {to_collectors}',
                    color=self.colors.send_to
                )
            )
        if field.collect_info:
            defined_collectors = ', '.join(field.collect_info)
            parts.append(
                self.template_renderer.render_template(
                    'html/colored_text.j2',
                    text=f'● collectors: {defined_collectors}',
                    color=self.colors.collector
                )
            )

        return parts

    def _render_schema_field(
        self,
        field: FieldInfo,
        max_type_length: int | None = None
    ) -> str:
        """Render a single schema field."""
        max_len = max_type_length or self.config.max_type_length

        # Truncate type name if too long
        type_name = field.type_name
        if len(type_name) > max_len:
            type_name = type_name[:max_len] + self.config.type_suffix

        # Format field display
        field_text = f'{field.name}: {type_name}'

        # Render pydantic metadata
        meta_parts = self._render_pydantic_meta_parts(field)
        meta_html = self.template_renderer.render_template(
            'html/pydantic_meta.j2',
            meta_parts=meta_parts
        )

        # Render field text (with strikethrough if excluded)
        text_html = self.template_renderer.render_template(
            'html/colored_text.j2',
            text=field_text,
            color='#000',  # Default color
            strikethrough=field.is_exclude
        )

        # Combine field text and metadata
        content = f'<font>  {text_html}  </font> {meta_html}'

        # Render the table row
        return self.template_renderer.render_template(
            'html/schema_field_row.j2',
            port=field.name,
            align='left',
            content=content
        )

    def _get_filtered_fields(self, node: SchemaNode) -> list[FieldInfo]:
        """Get fields filtered by show_fields and show_pydantic_resolve_meta settings."""

        # Filter fields based on pydantic-resolve meta setting
        if self.show_pydantic_resolve_meta:
            fields = [n for n in node.fields if n.has_pydantic_resolve_meta or not n.from_base]
        else:
            fields = [n for n in node.fields if not n.from_base]

        # Further filter by show_fields setting
        if self.show_fields == 'all':
            return fields
        elif self.show_fields == 'object':
            if self.show_pydantic_resolve_meta:
                # Show object fields or fields with pydantic-resolve metadata
                return [f for f in fields if f.is_object or f.has_pydantic_resolve_meta]
            else:
                # Show only object fields
                return [f for f in fields if f.is_object]
        else:  # 'single'
            return []

    def render_schema_label(self, node: SchemaNode, color: str | None = None) -> str:
        """
        Render a schema node's label as an HTML table.

        TODO: Improve logic with show_pydantic_resolve_meta
        """
        fields = self._get_filtered_fields(node)

        # Render field rows
        rows = []
        has_base_fields = any(f.from_base for f in node.fields)

        # Add inherited fields notice if needed
        if self.show_fields == 'all' and has_base_fields:
            notice = self.template_renderer.render_template(
                'html/colored_text.j2',
                text='  Inherited Fields ... ',
                color=self.colors.text_gray
            )
            rows.append(
                self.template_renderer.render_template(
                    'html/schema_field_row.j2',
                    content=notice,
                    align='left'
                )
            )

        # Render each field
        for field in fields:
            rows.append(self._render_schema_field(field))

        # Determine header color
        default_color = self.colors.primary if color is None else color
        header_color = self.colors.highlight if node.id == self.schema else default_color

        # Render header
        header = self.template_renderer.render_template(
            'html/schema_header.j2',
            text=node.name,
            bg_color=header_color,
            port=PK
        )

        # Render complete table
        return self.template_renderer.render_template(
            'html/schema_table.j2',
            header=header,
            rows=''.join(rows)
        )

    def _handle_schema_anchor(self, source: str) -> str:
        """Handle schema anchor for DOT links."""
        if '::' in source:
            a, b = source.split('::', 1)
            return f'"{a}":{b}'
        return f'"{source}"'

    def _format_link_attributes(self, attrs: dict) -> str:
        """Format link attributes for DOT format."""
        return ', '.join(f'{k}="{v}"' for k, v in attrs.items())

    def render_link(self, link: Link) -> str:
        """Render a link in DOT format."""
        source = self._handle_schema_anchor(link.source)
        target = self._handle_schema_anchor(link.target)

        # Build link attributes
        # If link.style is explicitly set (e.g., 'solid, dashed' for ER diagrams), use it
        # Otherwise, get default style from configuration based on link.type
        if link.style is not None:
            attrs = {'style': link.style}
            if link.label:
                attrs['label'] = link.label
            # attrs['minlen'] = 3
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

    def render_schema_node(self, node: SchemaNode, color: str | None = None) -> str:
        """Render a schema node in DOT format."""
        label = self.render_schema_label(node, color)

        return self.template_renderer.render_template(
            'dot/schema_node.j2',
            id=node.id,
            label=label,
            margin=self.style.node_margin
        )

    def render_tag_node(self, tag: Tag) -> str:
        """Render a tag node in DOT format."""
        return self.template_renderer.render_template(
            'dot/tag_node.j2',
            id=tag.id,
            name=tag.name,
            margin=self.style.node_margin
        )

    def render_route_node(self, route: Route) -> str:
        """Render a route node in DOT format."""
        # Truncate response schema if too long
        response_schema = route.response_schema
        if len(response_schema) > self.config.max_type_length:
            response_schema = response_schema[:self.config.max_type_length] + self.config.type_suffix

        return self.template_renderer.render_template(
            'dot/route_node.j2',
            id=route.id,
            name=route.name,
            response_schema=response_schema,
            margin=self.style.node_margin
        )

    def _render_module_schema(
        self,
        mod: ModuleNode,
        module_color_flag: set[str],
        inherit_color: str | None = None,
        show_cluster: bool = True
    ) -> str:
        """Render a module schema tree."""
        color = inherit_color
        cluster_color: str | None = None

        # Check if this module has a custom color
        for k in module_color_flag:
            if mod.fullname.startswith(k):
                module_color_flag.remove(k)
                color = self.module_color[k]
                cluster_color = color if color != inherit_color else None
                break

        # Render inner schema nodes
        inner_nodes = [
            self.render_schema_node(node, color)
            for node in mod.schema_nodes
        ]
        inner_nodes_str = '\n'.join(inner_nodes)

        # Recursively render child modules
        child_str = '\n'.join(
            self._render_module_schema(
                m,
                module_color_flag=module_color_flag,
                inherit_color=color,
                show_cluster=show_cluster
            )
            for m in mod.modules
        )

        if show_cluster:
            # Render as a cluster
            cluster_id = f'module_{mod.fullname.replace(".", "_")}'
            pen_style = ''

            if cluster_color:
                pen_style = f'pencolor = "{cluster_color}"'
                pen_style += '\n' + f'penwidth = 3' if color else ''
            else:
                pen_style = 'pencolor="#ccc"'

            return self.template_renderer.render_template(
                'dot/cluster.j2',
                cluster_id=cluster_id,
                label=mod.name,
                tooltip=mod.fullname,
                border_color=self.colors.border,
                pen_color=cluster_color,
                pen_width=3 if color and not cluster_color else None,
                content=f'{inner_nodes_str}\n{child_str}'
            )
        else:
            # Render without cluster
            return f'{inner_nodes_str}\n{child_str}'

    def render_module_schema_content(self, nodes: list[SchemaNode]) -> str:
        """Render all module schemas."""
        module_schemas = build_module_schema_tree(nodes)
        module_color_flag = set(self.module_color.keys())

        return '\n'.join(
            self._render_module_schema(
                m,
                module_color_flag=module_color_flag,
                show_cluster=self.show_module
            )
            for m in module_schemas
        )

    def _render_module_route(self, mod: ModuleRoute, show_cluster: bool = True) -> str:
        """Render a module route tree."""
        # Render inner route nodes
        inner_nodes = [self.render_route_node(r) for r in mod.routes]
        inner_nodes_str = '\n'.join(inner_nodes)

        # Recursively render child modules
        child_str = '\n'.join(
            self._render_module_route(m, show_cluster=show_cluster)
            for m in mod.modules
        )

        if show_cluster:
            cluster_id = f'route_module_{mod.fullname.replace(".", "_")}'

            return self.template_renderer.render_template(
                'dot/cluster.j2',
                cluster_id=cluster_id,
                label=mod.name,
                tooltip=mod.fullname,
                border_color=self.colors.border,
                pen_color=None,
                pen_width=None,
                content=f'{inner_nodes_str}\n{child_str}'
            )
        else:
            return f'{inner_nodes_str}\n{child_str}'

    def render_module_route_content(self, routes: list[Route]) -> str:
        """Render all module routes."""
        module_routes = build_module_route_tree(routes)

        return '\n'.join(
            self._render_module_route(m, show_cluster=self.show_module)
            for m in module_routes
        )

    def _render_cluster_container(
        self,
        name: str,
        label: str,
        content: str,
        fontsize: str | None = None
    ) -> str:
        """Render a cluster container (for tags, routes, schemas)."""
        return self.template_renderer.render_template(
            'dot/cluster_container.j2',
            name=name,
            label=label,
            content=content,
            border_color=self.colors.border,
            margin=self.style.cluster_margin,
            fontsize=fontsize or self.style.cluster_fontsize
        )

    def render_dot(
        self,
        tags: list[Tag],
        routes: list[Route],
        nodes: list[SchemaNode],
        links: list[Link],
        spline_line: bool = False
    ) -> str:
        """
        Render the complete DOT graph.

        Args:
            tags: List of tags
            routes: List of routes
            nodes: List of schema nodes
            links: List of links
            spline_line: Whether to use spline lines

        Returns:
            Complete DOT graph as a string
        """
        # Render tag nodes
        tag_str = '\n'.join(self.render_tag_node(t) for t in tags)

        # Render tags cluster
        tags_cluster = self._render_cluster_container(
            name='tags',
            label='Tags',
            content=tag_str
        )

        # Render routes cluster
        module_routes_str = self.render_module_route_content(routes)
        routes_cluster = self._render_cluster_container(
            name='router',
            label='Routes',
            content=module_routes_str
        )

        # Render schemas cluster
        module_schemas_str = self.render_module_schema_content(nodes)
        schemas_cluster = self._render_cluster_container(
            name='schema',
            label='Schema',
            content=module_schemas_str
        )

        # Render links
        link_str = '\n'.join(self.render_link(link) for link in links)

        # Render complete digraph
        return self.template_renderer.render_template(
            'dot/digraph.j2',
            pad=self.style.pad,
            nodesep=self.style.nodesep,
            spline='line' if spline_line else '',
            font=self.style.font,
            node_fontsize=self.style.node_fontsize,
            tags_cluster=tags_cluster,
            routes_cluster=routes_cluster,
            schemas_cluster=schemas_cluster,
            links=link_str
        )
