"""fastapi_voyager

Utilities to introspect a FastAPI application and visualize its routing tree.
"""
from .version import __version__  # noqa: F401

from .server import create_voyager

__all__ = ["__version__", "create_voyager"]
