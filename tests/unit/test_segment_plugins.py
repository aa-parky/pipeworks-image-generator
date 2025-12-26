"""Unit tests for segment plugin system."""

import gradio as gr
import pytest

from pipeworks.ui.segment_plugins import (
    SegmentPluginBase,
    SegmentPluginRegistry,
    SegmentUIComponents,
    segment_plugin_registry,
)


class TestSegmentPluginBase:
    """Tests for SegmentPluginBase abstract class."""

    def test_cannot_instantiate_base_class(self):
        """Base class cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SegmentPluginBase()

    def test_has_required_attributes(self):
        """Base class has required class attributes."""
        assert hasattr(SegmentPluginBase, "name")
        assert hasattr(SegmentPluginBase, "description")
        assert hasattr(SegmentPluginBase, "version")

    def test_has_required_methods(self):
        """Base class has required abstract methods."""
        assert hasattr(SegmentPluginBase, "create_ui")
        assert hasattr(SegmentPluginBase, "get_input_components")
        assert hasattr(SegmentPluginBase, "values_to_config")
        assert hasattr(SegmentPluginBase, "register_events")


class TestSegmentPluginRegistry:
    """Tests for SegmentPluginRegistry."""

    def test_registry_initialization(self):
        """Test registry initializes correctly."""
        registry = SegmentPluginRegistry()
        assert isinstance(registry._plugins, dict)
        assert len(registry._plugins) == 0

    def test_register_plugin_success(self):
        """Test successful plugin registration."""
        registry = SegmentPluginRegistry()

        # Create a concrete plugin for testing
        class TestPlugin(SegmentPluginBase):
            name = "Test Plugin"
            description = "Test plugin for unit tests"
            version = "1.0.0"

            def create_ui(self, segment_id, initial_choices):
                pass

            def get_input_components(self, components):
                pass

            def values_to_config(self, *values):
                pass

            def register_events(self, components, ui_state, event_handlers):
                pass

        registry.register(TestPlugin)
        assert "Test Plugin" in registry.list_available()

    def test_register_non_plugin_raises_error(self):
        """Test registering non-plugin class raises TypeError."""
        registry = SegmentPluginRegistry()

        class NotAPlugin:
            name = "Not a Plugin"

        with pytest.raises(TypeError, match="must inherit from SegmentPluginBase"):
            registry.register(NotAPlugin)

    def test_get_plugin_class_existing(self):
        """Test retrieving existing plugin class."""
        registry = SegmentPluginRegistry()

        class TestPlugin(SegmentPluginBase):
            name = "Test Plugin"
            description = "Test"
            version = "1.0.0"

            def create_ui(self, segment_id, initial_choices):
                pass

            def get_input_components(self, components):
                pass

            def values_to_config(self, *values):
                pass

            def register_events(self, components, ui_state, event_handlers):
                pass

        registry.register(TestPlugin)
        plugin_class = registry.get_plugin_class("Test Plugin")
        assert plugin_class == TestPlugin

    def test_get_plugin_class_nonexistent(self):
        """Test retrieving non-existent plugin returns None."""
        registry = SegmentPluginRegistry()
        plugin_class = registry.get_plugin_class("Nonexistent Plugin")
        assert plugin_class is None

    def test_list_available_empty(self):
        """Test listing available plugins when none registered."""
        registry = SegmentPluginRegistry()
        available = registry.list_available()
        assert isinstance(available, list)
        assert len(available) == 0

    def test_list_available_multiple(self):
        """Test listing multiple registered plugins."""
        registry = SegmentPluginRegistry()

        # Create multiple test plugins
        class Plugin1(SegmentPluginBase):
            name = "Plugin 1"
            description = "First plugin"
            version = "1.0.0"

            def create_ui(self, segment_id, initial_choices):
                pass

            def get_input_components(self, components):
                pass

            def values_to_config(self, *values):
                pass

            def register_events(self, components, ui_state, event_handlers):
                pass

        class Plugin2(SegmentPluginBase):
            name = "Plugin 2"
            description = "Second plugin"
            version = "1.0.0"

            def create_ui(self, segment_id, initial_choices):
                pass

            def get_input_components(self, components):
                pass

            def values_to_config(self, *values):
                pass

            def register_events(self, components, ui_state, event_handlers):
                pass

        registry.register(Plugin1)
        registry.register(Plugin2)

        available = registry.list_available()
        assert len(available) == 2
        assert "Plugin 1" in available
        assert "Plugin 2" in available
        # Check alphabetical sorting
        assert available == sorted(available)

    def test_register_overwrites_existing(self):
        """Test registering same name twice overwrites previous."""
        registry = SegmentPluginRegistry()

        class PluginV1(SegmentPluginBase):
            name = "Test"
            description = "Version 1"
            version = "1.0.0"

            def create_ui(self, segment_id, initial_choices):
                pass

            def get_input_components(self, components):
                pass

            def values_to_config(self, *values):
                pass

            def register_events(self, components, ui_state, event_handlers):
                pass

        class PluginV2(SegmentPluginBase):
            name = "Test"
            description = "Version 2"
            version = "2.0.0"

            def create_ui(self, segment_id, initial_choices):
                pass

            def get_input_components(self, components):
                pass

            def values_to_config(self, *values):
                pass

            def register_events(self, components, ui_state, event_handlers):
                pass

        registry.register(PluginV1)
        registry.register(PluginV2)

        plugin_class = registry.get_plugin_class("Test")
        assert plugin_class == PluginV2
        assert plugin_class.version == "2.0.0"


class TestSegmentUIComponents:
    """Tests for SegmentUIComponents dataclass."""

    def test_required_fields_present(self):
        """Test that all required fields are defined."""
        # This test checks the dataclass structure
        # We can create a mock instance to verify fields
        with gr.Blocks():
            components = SegmentUIComponents(
                segment_id="0",
                plugin_name="Test",
                container=gr.Group(),
                title=gr.Markdown("Test"),
                text=gr.Textbox(),
                file=gr.Dropdown(),
                path_state=gr.State(),
                path_display=gr.Textbox(),
                line_count_display=gr.Markdown(),
                mode=gr.Dropdown(),
                dynamic=gr.Checkbox(),
                text_order=gr.Radio(),
                delimiter=gr.Dropdown(),
                line=gr.Number(),
                range_end=gr.Number(),
                count=gr.Number(),
                sequential_start_line=gr.Number(),
            )

        assert components.segment_id == "0"
        assert components.plugin_name == "Test"
        assert components.title is not None
        assert components.text is not None
        assert components.file is not None

    def test_optional_condition_fields_default_none(self):
        """Test optional condition fields default to None."""
        with gr.Blocks():
            components = SegmentUIComponents(
                segment_id="0",
                plugin_name="Test",
                container=gr.Group(),
                title=gr.Markdown("Test"),
                text=gr.Textbox(),
                file=gr.Dropdown(),
                path_state=gr.State(),
                path_display=gr.Textbox(),
                line_count_display=gr.Markdown(),
                mode=gr.Dropdown(),
                dynamic=gr.Checkbox(),
                text_order=gr.Radio(),
                delimiter=gr.Dropdown(),
                line=gr.Number(),
                range_end=gr.Number(),
                count=gr.Number(),
                sequential_start_line=gr.Number(),
            )

        assert components.condition_type is None
        assert components.condition_text is None
        assert components.condition_regenerate is None
        assert components.condition_dynamic is None
        assert components.condition_controls is None

    def test_optional_condition_fields_can_be_set(self):
        """Test optional condition fields can be provided."""
        with gr.Blocks():
            components = SegmentUIComponents(
                segment_id="0",
                plugin_name="Test",
                container=gr.Group(),
                title=gr.Markdown("Test"),
                text=gr.Textbox(),
                file=gr.Dropdown(),
                path_state=gr.State(),
                path_display=gr.Textbox(),
                line_count_display=gr.Markdown(),
                mode=gr.Dropdown(),
                dynamic=gr.Checkbox(),
                text_order=gr.Radio(),
                delimiter=gr.Dropdown(),
                line=gr.Number(),
                range_end=gr.Number(),
                count=gr.Number(),
                sequential_start_line=gr.Number(),
                # Provide condition fields
                condition_type=gr.Dropdown(),
                condition_text=gr.Textbox(),
                condition_regenerate=gr.Button(),
                condition_dynamic=gr.Checkbox(),
                condition_controls=gr.Row(),
            )

        assert components.condition_type is not None
        assert components.condition_text is not None
        assert components.condition_regenerate is not None
        assert components.condition_dynamic is not None
        assert components.condition_controls is not None


class TestGlobalRegistry:
    """Tests for global segment_plugin_registry instance."""

    def test_global_registry_exists(self):
        """Test global registry instance exists."""
        assert segment_plugin_registry is not None
        assert isinstance(segment_plugin_registry, SegmentPluginRegistry)

    def test_global_registry_is_singleton(self):
        """Test global registry behaves as singleton."""
        # Import again to get the same instance
        from pipeworks.ui.segment_plugins import segment_plugin_registry as registry2

        assert segment_plugin_registry is registry2
