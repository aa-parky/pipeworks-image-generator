"""Base classes and registry for the Pipeworks segment plugin system.

This module provides the foundation for creating segment plugins that can be
dynamically added to the prompt builder UI. Each segment plugin defines:
- UI component creation
- Value conversion to SegmentConfig
- Event handler registration

The segment plugin system enables users to add/remove prompt segments as needed,
rather than being locked into a fixed grid of segments.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import gradio as gr

from ..models import SegmentConfig

logger = logging.getLogger(__name__)


@dataclass
class SegmentUIComponents:
    """Container for segment UI components.

    All segment plugins return this structure for consistency.
    This dataclass holds all Gradio components that make up a segment.

    Attributes
    ----------
    segment_id : str
        Unique identifier for this segment (e.g., "0", "1", "2")
    plugin_name : str
        Name of the plugin that created this segment
    container : gr.Group
        Gradio Group container holding all components (for removal)

    # Core components (present in all segments)
    title : gr.Markdown
        Segment title with status indicators
    text : gr.Textbox
        Manual text input
    file : gr.Dropdown
        File/folder browser dropdown
    path_state : gr.State
        Hidden state tracking current browser path
    path_display : gr.Textbox
        Display of current path (read-only)
    line_count_display : gr.Markdown
        Display of file line count when file selected
    mode : gr.Dropdown
        Selection mode (Random Line, Specific Line, etc.)
    dynamic : gr.Checkbox
        Whether to rebuild this segment per image
    text_order : gr.Radio
        Text before or after file content
    delimiter : gr.Dropdown
        Delimiter for joining text and file content
    line : gr.Number
        Line number for Specific Line mode
    range_end : gr.Number
        End line for Line Range mode
    count : gr.Number
        Count for Random Multiple mode
    sequential_start_line : gr.Number
        Starting line for Sequential mode

    # Condition components (optional, None if not supported)
    condition_type : gr.Dropdown | None
        Condition type selector (None/Character/Facial/Both)
    condition_text : gr.Textbox | None
        Generated condition text
    condition_regenerate : gr.Button | None
        Button to regenerate conditions
    condition_dynamic : gr.Checkbox | None
        Whether to regenerate conditions per run
    condition_controls : gr.Row | None
        Container for condition controls (visibility toggle)
    """

    segment_id: str
    plugin_name: str
    container: gr.Group

    # Core components (all segments)
    title: gr.Markdown
    text: gr.Textbox
    file: gr.Dropdown
    path_state: gr.State
    path_display: gr.Textbox
    line_count_display: gr.Markdown
    mode: gr.Dropdown
    dynamic: gr.Checkbox
    text_order: gr.Radio
    delimiter: gr.Dropdown
    line: gr.Number
    range_end: gr.Number
    count: gr.Number
    sequential_start_line: gr.Number

    # Condition components (optional, None if not supported)
    condition_type: gr.Dropdown | None = None
    condition_text: gr.Textbox | None = None
    condition_regenerate: gr.Button | None = None
    condition_dynamic: gr.Checkbox | None = None
    condition_controls: gr.Row | None = None


class SegmentPluginBase(ABC):
    """Base class for all segment plugins.

    Segment plugins define how to create a segment UI, convert values to
    SegmentConfig, and register event handlers. This enables extensibility
    while maintaining a consistent interface.

    Subclasses must implement all abstract methods to define their
    segment behavior.

    Attributes
    ----------
    name : str
        Human-readable plugin name (e.g., "Complete Segment")
    description : str
        Description of what this segment plugin provides
    version : str
        Plugin version (semantic versioning)

    Examples
    --------
    Create a custom segment plugin:

        >>> class MySegmentPlugin(SegmentPluginBase):
        ...     name = "My Segment"
        ...     description = "Custom segment with special features"
        ...     version = "1.0.0"
        ...
        ...     def create_ui(self, segment_id, initial_choices):
        ...         # Create Gradio components
        ...         ...
        ...         return SegmentUIComponents(...)
        ...
        ...     def get_input_components(self, components):
        ...         return [components.text, components.file, ...]
        ...
        ...     def values_to_config(self, *values):
        ...         return SegmentConfig(...)
        ...
        ...     def register_events(self, components, ui_state, event_handlers):
        ...         # Wire up event handlers
        ...         components.file.change(...)

    Register the plugin:

        >>> segment_plugin_registry.register(MySegmentPlugin)
    """

    name: str = "Base Segment"
    description: str = "Base segment plugin"
    version: str = "0.1.0"

    @abstractmethod
    def create_ui(self, segment_id: str, initial_choices: list[str]) -> SegmentUIComponents:
        """Create UI components for this segment type.

        This method creates all Gradio components needed for the segment
        and returns them wrapped in a SegmentUIComponents dataclass.

        Args:
            segment_id: Unique identifier (e.g., "0", "1", "2")
            initial_choices: File browser initial choices (files/folders)

        Returns:
            SegmentUIComponents with all Gradio components

        Notes:
            - Must create components within a gr.Group() or gr.Column() context
            - The container must be stored in components.container
            - All standard components must be created (text, file, mode, etc.)
            - Condition components are optional (can be None)
        """
        pass

    @abstractmethod
    def get_input_components(self, components: SegmentUIComponents) -> list[gr.Component]:
        """Return components used as function inputs.

        This method returns the list of Gradio components that should be
        passed as inputs to event handlers (e.g., build_prompt, generate_image).

        Args:
            components: SegmentUIComponents created by create_ui()

        Returns:
            List of Gradio components in the order expected by handlers

        Notes:
            - Order matters! Must match values_to_config() parameter order
            - Typically 11 components for basic segment, 14 for complete segment
            - Standard order: text, path_state, file, mode, line, range_end,
              count, dynamic, sequential_start_line, text_order, delimiter,
              [condition_type, condition_text, condition_dynamic]
        """
        pass

    @abstractmethod
    def values_to_config(self, *values) -> SegmentConfig:
        """Convert UI values to SegmentConfig.

        This method takes the raw values from UI components (in the same
        order as get_input_components) and converts them to a SegmentConfig
        dataclass instance.

        Args:
            *values: Variable number of values from get_input_components()

        Returns:
            SegmentConfig instance with all values populated

        Notes:
            - Values order must match get_input_components()
            - Handle type conversion (str to int, etc.)
            - Provide sensible defaults for missing values
        """
        pass

    @abstractmethod
    def register_events(
        self,
        components: SegmentUIComponents,
        ui_state: gr.State,
        event_handlers: dict,
    ) -> None:
        """Register event handlers for this segment.

        This method wires up all event handlers (file navigation, mode changes,
        condition generation, etc.) for the segment's components.

        Args:
            components: SegmentUIComponents created by create_ui()
            ui_state: Global UI state (gr.State)
            event_handlers: Dict of handler functions with keys:
                - "navigate_file_selection": File browser navigation
                - "update_mode_visibility": Mode-specific input visibility
                - "toggle_condition_type": Condition type selection
                - "regenerate_condition": Condition regeneration
                - (Additional handlers may be added as needed)

        Returns:
            None (events are registered as side effects)

        Notes:
            - Use Gradio's .change(), .click(), .submit() methods
            - Chain events with .then() when needed
            - Only register condition events if condition_type is not None
        """
        pass


class SegmentPluginRegistry:
    """Registry for segment plugins.

    This singleton manages registration and retrieval of segment plugins.
    Plugins register themselves by calling registry.register(PluginClass).

    Examples
    --------
    Register a plugin:

        >>> segment_plugin_registry.register(CompleteSegmentPlugin)

    Get plugin class:

        >>> plugin_class = segment_plugin_registry.get_plugin_class("Complete Segment")
        >>> plugin_instance = plugin_class()

    List available plugins:

        >>> available = segment_plugin_registry.list_available()
        >>> print(available)
        ['Complete Segment', 'Basic Segment']
    """

    def __init__(self):
        """Initialize empty plugin registry."""
        self._plugins: dict[str, type[SegmentPluginBase]] = {}
        logger.info("Initialized segment plugin registry")

    def register(self, plugin_class: type[SegmentPluginBase]) -> None:
        """Register a segment plugin class.

        Args:
            plugin_class: Plugin class to register (must inherit from SegmentPluginBase)

        Raises:
            TypeError: If plugin_class doesn't inherit from SegmentPluginBase

        Notes:
            - Plugin name is used as the key (must be unique)
            - Registering the same name twice will overwrite the previous plugin
        """
        if not issubclass(plugin_class, SegmentPluginBase):
            raise TypeError(f"{plugin_class.__name__} must inherit from SegmentPluginBase")

        plugin_name = plugin_class.name
        self._plugins[plugin_name] = plugin_class
        logger.info(f"Registered segment plugin: {plugin_name} (v{plugin_class.version})")

    def get_plugin_class(self, name: str) -> type[SegmentPluginBase] | None:
        """Get plugin class by name.

        Args:
            name: Plugin name (e.g., "Complete Segment")

        Returns:
            Plugin class if found, None otherwise

        Examples:
            >>> plugin_class = registry.get_plugin_class("Complete Segment")
            >>> if plugin_class:
            ...     instance = plugin_class()
        """
        return self._plugins.get(name)

    def list_available(self) -> list[str]:
        """List all registered plugin names.

        Returns:
            List of plugin names sorted alphabetically

        Examples:
            >>> plugins = registry.list_available()
            >>> for name in plugins:
            ...     print(f"Available: {name}")
        """
        return sorted(self._plugins.keys())


# Global registry instance
segment_plugin_registry = SegmentPluginRegistry()
