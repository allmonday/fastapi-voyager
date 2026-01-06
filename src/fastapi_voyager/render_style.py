"""
Style constants and configuration for rendering DOT graphs and HTML tables.
"""
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ColorScheme:
    """Color scheme for graph visualization."""

    # Node colors
    primary: str = '#009485'
    highlight: str = 'tomato'

    # Pydantic-resolve metadata colors
    resolve: str = '#47a80f'
    post: str = '#427fa4'
    expose_as: str = '#895cb9'
    send_to: str = '#ca6d6d'
    collector: str = '#777'

    # Link colors
    inherit: str = 'purple'
    subset: str = 'orange'

    # Border colors
    border: str = '#666'
    cluster_border: str = '#ccc'

    # Text colors
    text_gray: str = '#999'


@dataclass
class GraphvizStyle:
    """Graphviz DOT style configuration."""

    # Font settings
    font: str = 'Helvetica,Arial,sans-serif'
    node_fontsize: str = '16'
    cluster_fontsize: str = '20'

    # Layout settings
    nodesep: str = '0.8'
    pad: str = '0.5'
    node_margin: str = '0.5,0.1'
    cluster_margin: str = '18'

    # Link styles configuration
    LINK_STYLES: dict[str, dict] = field(default_factory=lambda: {
        'tag_route': {
            'style': 'solid',
            'minlen': 3,
        },
        'route_to_schema': {
            'style': 'solid',
            'dir': 'back',
            'arrowtail': 'odot',
            'minlen': 3,
        },
        'schema': {
            'style': 'solid',
            'label': '',
            'dir': 'back',
            'minlen': 3,
            'arrowtail': 'odot',
        },
        'parent': {
            'style': 'solid,dashed',
            'dir': 'back',
            'minlen': 3,
            'taillabel': '< inherit >',
            'color': 'purple',
            'tailport': 'n',
        },
        'subset': {
            'style': 'solid,dashed',
            'dir': 'back',
            'minlen': 3,
            'taillabel': '< subset >',
            'color': 'orange',
            'tailport': 'n',
        },
        'tag_to_schema': {
            'style': 'solid',
            'minlen': 3,
        },
    })

    def get_link_attributes(self, link_type: str) -> dict:
        """Get link style attributes for a given link type."""
        return self.LINK_STYLES.get(link_type, {})


@dataclass
class RenderConfig:
    """Complete rendering configuration."""

    colors: ColorScheme = field(default_factory=ColorScheme)
    style: GraphvizStyle = field(default_factory=GraphvizStyle)

    # Field display settings
    max_type_length: int = 25
    type_suffix: str = '..'
