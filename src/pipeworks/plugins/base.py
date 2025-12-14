"""Base classes and registry for the Pipeworks plugin system."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Type

from PIL import Image

logger = logging.getLogger(__name__)


class PluginBase(ABC):
    """
    Base class for all Pipeworks plugins.

    Plugins can hook into different stages of the generation process:
    - Before generation starts
    - After generation completes
    - Before saving
    - After saving
    """

    name: str = "Base Plugin"
    description: str = "Base plugin class"
    version: str = "0.1.0"

    def __init__(self, **config):
        """
        Initialize the plugin with configuration.

        Args:
            **config: Plugin-specific configuration parameters
        """
        self.config = config
        self.enabled = True
        logger.info(f"Initialized plugin: {self.name}")

    def on_generate_start(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Called before generation starts.

        Args:
            params: Generation parameters (prompt, width, height, seed, etc.)

        Returns:
            Modified parameters (or original if no changes)
        """
        return params

    def on_generate_complete(
        self, image: Image.Image, params: Dict[str, Any]
    ) -> Image.Image:
        """
        Called after generation completes but before saving.

        Args:
            image: Generated image
            params: Generation parameters used

        Returns:
            Modified image (or original if no changes)
        """
        return image

    def on_before_save(
        self, image: Image.Image, save_path: Path, params: Dict[str, Any]
    ) -> tuple[Image.Image, Path]:
        """
        Called before saving the image.

        Args:
            image: Image to be saved
            save_path: Proposed save path
            params: Generation parameters

        Returns:
            Tuple of (possibly modified image, possibly modified save path)
        """
        return image, save_path

    def on_after_save(
        self, image: Image.Image, save_path: Path, params: Dict[str, Any]
    ) -> None:
        """
        Called after the image has been saved.

        Args:
            image: Saved image
            save_path: Actual save path
            params: Generation parameters
        """
        pass

    def enable(self) -> None:
        """Enable this plugin."""
        self.enabled = True
        logger.info(f"Enabled plugin: {self.name}")

    def disable(self) -> None:
        """Disable this plugin."""
        self.enabled = False
        logger.info(f"Disabled plugin: {self.name}")


class PluginRegistry:
    """Registry for managing available plugins."""

    def __init__(self):
        self._plugins: Dict[str, Type[PluginBase]] = {}
        self._instances: Dict[str, PluginBase] = {}

    def register(self, plugin_class: Type[PluginBase]) -> None:
        """
        Register a plugin class.

        Args:
            plugin_class: Plugin class to register
        """
        plugin_name = plugin_class.name
        self._plugins[plugin_name] = plugin_class
        logger.info(f"Registered plugin: {plugin_name}")

    def instantiate(
        self, plugin_name: str, **config
    ) -> Optional[PluginBase]:
        """
        Create an instance of a registered plugin.

        Args:
            plugin_name: Name of the plugin to instantiate
            **config: Configuration for the plugin

        Returns:
            Plugin instance or None if not found
        """
        if plugin_name not in self._plugins:
            logger.error(f"Plugin not found: {plugin_name}")
            return None

        instance = self._plugins[plugin_name](**config)
        self._instances[plugin_name] = instance
        return instance

    def get_instance(self, plugin_name: str) -> Optional[PluginBase]:
        """Get an existing plugin instance."""
        return self._instances.get(plugin_name)

    def list_available(self) -> list[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())

    def get_all_instances(self) -> list[PluginBase]:
        """Get all instantiated plugins."""
        return list(self._instances.values())


# Global plugin registry
plugin_registry = PluginRegistry()
