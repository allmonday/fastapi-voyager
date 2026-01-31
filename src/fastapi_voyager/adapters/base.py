"""
Base adapter interface for framework-agnostic voyager server.

This module defines the abstract interface that all framework adapters must implement.
"""
from abc import ABC, abstractmethod
from typing import Any


class VoyagerAdapter(ABC):
    """
    Abstract base class for framework-specific voyager adapters.

    Each adapter is responsible for:
    1. Creating routes/endpoints for the voyager UI
    2. Handling HTTP requests and responses in a framework-specific way
    3. Returning an object that can be mounted/integrated with the target app
    """

    @abstractmethod
    def create_app(self) -> Any:
        """
        Create and return a framework-specific application object.

        The returned object should be mountable/integrable with the target framework.
        For example:
        - FastAPI: returns a FastAPI app
        - Django Ninja: returns an ASGI application
        - Litestar: returns a Litestar app

        Returns:
            A framework-specific application object
        """
        pass

    @abstractmethod
    def get_mount_path(self) -> str:
        """
        Get the recommended mount path for the voyager UI.

        Returns:
            The path where voyager should be mounted (e.g., "/voyager")
        """
        pass
