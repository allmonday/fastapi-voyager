"""
Framework adapters for fastapi-voyager.

This module provides adapters that allow voyager to work with different web frameworks.
"""
from fastapi_voyager.adapters.base import VoyagerAdapter
from fastapi_voyager.adapters.django_ninja_adapter import DjangoNinjaAdapter
from fastapi_voyager.adapters.fastapi_adapter import FastAPIAdapter
from fastapi_voyager.adapters.litestar_adapter import LitestarAdapter

__all__ = [
    "VoyagerAdapter",
    "FastAPIAdapter",
    "DjangoNinjaAdapter",
    "LitestarAdapter",
]
