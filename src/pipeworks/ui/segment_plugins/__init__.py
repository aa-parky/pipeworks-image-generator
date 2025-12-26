"""Segment plugin system for Pipeworks.

This package provides a plugin architecture for prompt builder segments,
enabling users to dynamically add/remove segments with full capabilities
(text, files, character/facial conditions).

The plugin system consists of:
- SegmentPluginBase: Abstract base class for all segment plugins
- SegmentUIComponents: Dataclass container for UI components
- SegmentPluginRegistry: Singleton registry for plugin management
- CompleteSegmentPlugin: Full-featured implementation (text + files + conditions)

Example Usage
-------------
Get available plugins:

    >>> from pipeworks.ui.segment_plugins import segment_plugin_registry
    >>> available = segment_plugin_registry.list_available()
    >>> print(available)
    ['Complete Segment']

Create a segment:

    >>> plugin_class = segment_plugin_registry.get_plugin_class("Complete Segment")
    >>> plugin = plugin_class()
    >>> with gr.Blocks():
    ...     components = plugin.create_ui("0", ["test.txt"])
    ...     inputs = plugin.get_input_components(components)

Custom Plugin
-------------
Create your own segment plugin:

    >>> from pipeworks.ui.segment_plugins import SegmentPluginBase, segment_plugin_registry
    >>>
    >>> class MyPlugin(SegmentPluginBase):
    ...     name = "My Plugin"
    ...     description = "Custom segment with special features"
    ...     version = "1.0.0"
    ...     # ... implement abstract methods ...
    >>>
    >>> segment_plugin_registry.register(MyPlugin)
"""

from .base import (
    SegmentPluginBase,
    SegmentPluginRegistry,
    SegmentUIComponents,
    segment_plugin_registry,
)
from .complete_segment import CompleteSegmentPlugin

__all__ = [
    "SegmentPluginBase",
    "SegmentPluginRegistry",
    "SegmentUIComponents",
    "segment_plugin_registry",
    "CompleteSegmentPlugin",
]
