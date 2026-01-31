"""
Introspectors for different web frameworks.

This package contains built-in introspector implementations for various frameworks.
"""
from .base import AppIntrospector, RouteInfo

# Try to import each introspector, but don't fail if the framework isn't installed
try:
    from .fastapi import FastAPIIntrospector
except ImportError:
    FastAPIIntrospector = None  # type: ignore

try:
    from .django_ninja import DjangoNinjaIntrospector
except ImportError:
    DjangoNinjaIntrospector = None  # type: ignore

try:
    from .litestar import LitestarIntrospector
except ImportError:
    LitestarIntrospector = None  # type: ignore

__all__ = [
    "AppIntrospector",
    "RouteInfo",
    "FastAPIIntrospector",
    "DjangoNinjaIntrospector",
    "LitestarIntrospector",
]
