"""fastapi_voyager

Utilities to introspect web applications and visualize their routing tree.
"""
from .server import create_voyager
from .version import __version__  # noqa: F401

__all__ = [ "__version__", "create_voyager" ]
