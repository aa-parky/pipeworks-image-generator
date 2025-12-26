"""Unit tests for CompleteSegmentPlugin."""

import gradio as gr
import pytest

from pipeworks.ui.models import SegmentConfig
from pipeworks.ui.segment_plugins import (
    CompleteSegmentPlugin,
    SegmentUIComponents,
    segment_plugin_registry,
)


class TestCompleteSegmentPluginMetadata:
    """Tests for CompleteSegmentPlugin class metadata."""

    def test_plugin_name(self):
        """Test plugin has correct name."""
        plugin = CompleteSegmentPlugin()
        assert plugin.name == "Complete Segment"

    def test_plugin_description(self):
        """Test plugin has description."""
        plugin = CompleteSegmentPlugin()
        assert len(plugin.description) > 0
        assert "text" in plugin.description.lower()
        assert "condition" in plugin.description.lower()

    def test_plugin_version(self):
        """Test plugin has semantic version."""
        plugin = CompleteSegmentPlugin()
        assert plugin.version == "1.0.0"


class TestCompleteSegmentPluginRegistration:
    """Tests for CompleteSegmentPlugin auto-registration."""

    def test_plugin_auto_registered(self):
        """Test plugin is automatically registered on import."""
        # Plugin should be auto-registered when module is imported
        assert "Complete Segment" in segment_plugin_registry.list_available()

    def test_can_get_plugin_from_registry(self):
        """Test plugin can be retrieved from registry."""
        plugin_class = segment_plugin_registry.get_plugin_class("Complete Segment")
        assert plugin_class == CompleteSegmentPlugin

    def test_can_instantiate_from_registry(self):
        """Test plugin can be instantiated via registry."""
        plugin_class = segment_plugin_registry.get_plugin_class("Complete Segment")
        plugin = plugin_class()
        assert isinstance(plugin, CompleteSegmentPlugin)


class TestCompleteSegmentPluginCreateUI:
    """Tests for create_ui() method."""

    def test_create_ui_returns_segment_ui_components(self):
        """Test create_ui returns SegmentUIComponents."""
        plugin = CompleteSegmentPlugin()
        with gr.Blocks():
            components = plugin.create_ui("0", ["test.txt"])

        assert isinstance(components, SegmentUIComponents)

    def test_create_ui_sets_segment_id(self):
        """Test create_ui sets correct segment_id."""
        plugin = CompleteSegmentPlugin()
        with gr.Blocks():
            components = plugin.create_ui("5", ["test.txt"])

        assert components.segment_id == "5"

    def test_create_ui_sets_plugin_name(self):
        """Test create_ui sets correct plugin_name."""
        plugin = CompleteSegmentPlugin()
        with gr.Blocks():
            components = plugin.create_ui("0", [])

        assert components.plugin_name == "Complete Segment"

    def test_create_ui_creates_all_standard_components(self):
        """Test create_ui creates all required standard components."""
        plugin = CompleteSegmentPlugin()
        with gr.Blocks():
            components = plugin.create_ui("0", [])

        # Check all standard components exist
        assert components.container is not None
        assert components.title is not None
        assert components.text is not None
        assert components.file is not None
        assert components.path_state is not None
        assert components.path_display is not None
        assert components.line_count_display is not None
        assert components.mode is not None
        assert components.dynamic is not None
        assert components.text_order is not None
        assert components.delimiter is not None
        assert components.line is not None
        assert components.range_end is not None
        assert components.count is not None
        assert components.sequential_start_line is not None

    def test_create_ui_creates_all_condition_components(self):
        """Test create_ui creates all condition components."""
        plugin = CompleteSegmentPlugin()
        with gr.Blocks():
            components = plugin.create_ui("0", [])

        # Check all condition components exist
        assert components.condition_type is not None
        assert components.condition_text is not None
        assert components.condition_regenerate is not None
        assert components.condition_dynamic is not None
        assert components.condition_controls is not None

    def test_create_ui_with_initial_choices(self):
        """Test create_ui uses initial_choices for file dropdown."""
        plugin = CompleteSegmentPlugin()
        choices = ["(None)", "file1.txt", "file2.txt", "📁 folder1"]

        with gr.Blocks():
            components = plugin.create_ui("0", choices)

        # File dropdown should use provided choices
        assert components.file is not None

    def test_create_ui_multiple_segments_unique_ids(self):
        """Test create_ui creates segments with different IDs."""
        plugin = CompleteSegmentPlugin()

        with gr.Blocks():
            comp1 = plugin.create_ui("0", [])
            comp2 = plugin.create_ui("1", [])
            comp3 = plugin.create_ui("2", [])

        assert comp1.segment_id == "0"
        assert comp2.segment_id == "1"
        assert comp3.segment_id == "2"


class TestCompleteSegmentPluginGetInputComponents:
    """Tests for get_input_components() method."""

    def test_get_input_components_returns_list(self):
        """Test get_input_components returns a list."""
        plugin = CompleteSegmentPlugin()
        with gr.Blocks():
            components = plugin.create_ui("0", [])
            inputs = plugin.get_input_components(components)

        assert isinstance(inputs, list)

    def test_get_input_components_count(self):
        """Test get_input_components returns 14 components."""
        plugin = CompleteSegmentPlugin()
        with gr.Blocks():
            components = plugin.create_ui("0", [])
            inputs = plugin.get_input_components(components)

        # Should return 14 components (11 standard + 3 condition)
        assert len(inputs) == 14

    def test_get_input_components_order(self):
        """Test get_input_components returns components in correct order."""
        plugin = CompleteSegmentPlugin()
        with gr.Blocks():
            components = plugin.create_ui("0", [])
            inputs = plugin.get_input_components(components)

        # Check order matches expected
        assert inputs[0] == components.text
        assert inputs[1] == components.path_state
        assert inputs[2] == components.file
        assert inputs[3] == components.mode
        assert inputs[4] == components.line
        assert inputs[5] == components.range_end
        assert inputs[6] == components.count
        assert inputs[7] == components.dynamic
        assert inputs[8] == components.sequential_start_line
        assert inputs[9] == components.text_order
        assert inputs[10] == components.delimiter
        assert inputs[11] == components.condition_type
        assert inputs[12] == components.condition_text
        assert inputs[13] == components.condition_dynamic

    def test_get_input_components_all_gradio_components(self):
        """Test get_input_components returns only Gradio components."""
        plugin = CompleteSegmentPlugin()
        with gr.Blocks():
            components = plugin.create_ui("0", [])
            inputs = plugin.get_input_components(components)

        # All items should be Gradio components
        for component in inputs:
            assert hasattr(component, "__class__")
            # Check it's a Gradio component type
            assert "gradio" in str(type(component)).lower()


class TestCompleteSegmentPluginValuesToConfig:
    """Tests for values_to_config() method."""

    def test_values_to_config_returns_segment_config(self):
        """Test values_to_config returns SegmentConfig."""
        plugin = CompleteSegmentPlugin()
        values = (
            "test text",
            "",
            "(None)",
            "Random Line",
            1,
            1,
            1,
            False,
            1,
            "text_first",
            "Space ( )",
            "None",
            "",
            False,
        )

        config = plugin.values_to_config(*values)
        assert isinstance(config, SegmentConfig)

    def test_values_to_config_all_fields(self):
        """Test values_to_config populates all fields correctly."""
        plugin = CompleteSegmentPlugin()
        values = (
            "my prompt text",
            "styles",
            "realistic.txt",
            "Specific Line",
            5,
            10,
            3,
            True,
            2,
            "file_first",
            "Comma-Space (, )",
            "Character",
            "wiry, poor, old",
            True,
        )

        config = plugin.values_to_config(*values)

        assert config.text == "my prompt text"
        assert config.path == "styles"
        assert config.file == "realistic.txt"
        assert config.mode == "Specific Line"
        assert config.line == 5
        assert config.range_end == 10
        assert config.count == 3
        assert config.dynamic is True
        assert config.sequential_start_line == 2
        assert config.text_order == "file_first"
        assert config.delimiter == "Comma-Space (, )"
        assert config.condition_type == "Character"
        assert config.condition_text == "wiry, poor, old"
        assert config.condition_dynamic is True

    def test_values_to_config_no_conditions(self):
        """Test values_to_config with conditions disabled."""
        plugin = CompleteSegmentPlugin()
        values = (
            "text",
            "",
            "file.txt",
            "Random Line",
            1,
            1,
            1,
            False,
            1,
            "text_first",
            "Space ( )",
            "None",
            "",
            False,
        )

        config = plugin.values_to_config(*values)

        assert config.condition_type == "None"
        assert config.condition_text == ""
        assert config.condition_dynamic is False

    def test_values_to_config_character_conditions(self):
        """Test values_to_config with character conditions."""
        plugin = CompleteSegmentPlugin()
        values = (
            "a warrior",
            "",
            "(None)",
            "Random Line",
            1,
            1,
            1,
            False,
            1,
            "text_first",
            "Space ( )",
            "Character",
            "stocky, wealthy, alert",
            False,
        )

        config = plugin.values_to_config(*values)

        assert config.condition_type == "Character"
        assert config.condition_text == "stocky, wealthy, alert"
        assert config.text == "a warrior"

    def test_values_to_config_facial_conditions(self):
        """Test values_to_config with facial conditions."""
        plugin = CompleteSegmentPlugin()
        values = (
            "",
            "",
            "(None)",
            "Random Line",
            1,
            1,
            1,
            False,
            1,
            "text_first",
            "Space ( )",
            "Facial",
            "weathered",
            True,
        )

        config = plugin.values_to_config(*values)

        assert config.condition_type == "Facial"
        assert config.condition_text == "weathered"
        assert config.condition_dynamic is True

    def test_values_to_config_both_conditions(self):
        """Test values_to_config with both character and facial conditions."""
        plugin = CompleteSegmentPlugin()
        values = (
            "portrait",
            "",
            "(None)",
            "Random Line",
            1,
            1,
            1,
            False,
            1,
            "text_first",
            "Space ( )",
            "Both",
            "wiry, poor, weathered",
            False,
        )

        config = plugin.values_to_config(*values)

        assert config.condition_type == "Both"
        assert "wiry" in config.condition_text
        assert "weathered" in config.condition_text

    def test_values_to_config_number_conversion(self):
        """Test values_to_config converts number strings to int."""
        plugin = CompleteSegmentPlugin()
        values = (
            "text",
            "",
            "file.txt",
            "Line Range",
            "3",  # String instead of int
            "7",  # String instead of int
            "2",  # String instead of int
            False,
            "5",  # String instead of int
            "text_first",
            "Space ( )",
            "None",
            "",
            False,
        )

        config = plugin.values_to_config(*values)

        assert config.line == 3
        assert config.range_end == 7
        assert config.count == 2
        assert config.sequential_start_line == 5

    def test_values_to_config_empty_numbers_default_to_one(self):
        """Test values_to_config uses default 1 for empty number fields."""
        plugin = CompleteSegmentPlugin()
        values = (
            "text",
            "",
            "file.txt",
            "Random Line",
            None,  # Empty line
            None,  # Empty range_end
            None,  # Empty count
            False,
            None,  # Empty sequential_start_line
            "text_first",
            "Space ( )",
            "None",
            "",
            False,
        )

        config = plugin.values_to_config(*values)

        assert config.line == 1
        assert config.range_end == 1
        assert config.count == 1
        assert config.sequential_start_line == 1

    def test_values_to_config_wrong_count_raises_error(self):
        """Test values_to_config raises error with wrong number of values."""
        plugin = CompleteSegmentPlugin()

        # Too few values
        with pytest.raises(ValueError, match="Expected 14 values"):
            plugin.values_to_config("text", "", "file.txt")

        # Too many values
        with pytest.raises(ValueError, match="Expected 14 values"):
            plugin.values_to_config(*["value"] * 20)

    def test_values_to_config_preserves_empty_strings(self):
        """Test values_to_config preserves empty strings."""
        plugin = CompleteSegmentPlugin()
        values = (
            "",  # Empty text
            "",  # Empty path
            "(None)",
            "Random Line",
            1,
            1,
            1,
            False,
            1,
            "text_first",
            "Space ( )",
            "None",
            "",  # Empty condition_text
            False,
        )

        config = plugin.values_to_config(*values)

        assert config.text == ""
        assert config.path == ""
        assert config.condition_text == ""


class TestCompleteSegmentPluginRegisterEvents:
    """Tests for register_events() method."""

    def test_register_events_requires_event_handlers(self):
        """Test register_events requires event_handlers dict."""
        plugin = CompleteSegmentPlugin()

        with gr.Blocks():
            components = plugin.create_ui("0", [])
            ui_state = gr.State()

            # Should raise KeyError if handlers missing
            with pytest.raises(KeyError):
                plugin.register_events(components, ui_state, {})

    def test_register_events_with_all_handlers(self):
        """Test register_events works with all required handlers."""
        plugin = CompleteSegmentPlugin()

        # Create mock handlers
        def mock_navigate(file, path, state):
            return file, path, "", state

        def mock_update_visibility(mode):
            return {"visible": False}, {"visible": False}, {"visible": False}, {"visible": False}

        def mock_toggle_condition(condition_type):
            return "", {"visible": False}

        def mock_regenerate(condition_type):
            return ""

        event_handlers = {
            "navigate_file_selection": mock_navigate,
            "update_mode_visibility": mock_update_visibility,
            "toggle_condition_type": mock_toggle_condition,
            "regenerate_condition": mock_regenerate,
        }

        with gr.Blocks():
            components = plugin.create_ui("0", [])
            ui_state = gr.State()

            # Should not raise error with all handlers
            plugin.register_events(components, ui_state, event_handlers)

    def test_register_events_handles_missing_condition_components(self):
        """Test register_events gracefully handles missing condition components."""
        plugin = CompleteSegmentPlugin()

        # Create mock handlers
        def mock_navigate(file, path, state):
            return file, path, "", state

        def mock_update_visibility(mode):
            return {"visible": False}, {"visible": False}, {"visible": False}, {"visible": False}

        event_handlers = {
            "navigate_file_selection": mock_navigate,
            "update_mode_visibility": mock_update_visibility,
            # Missing condition handlers
        }

        with gr.Blocks():
            components = plugin.create_ui("0", [])
            # Manually set condition_type to None to simulate basic segment
            components_without_conditions = SegmentUIComponents(
                segment_id=components.segment_id,
                plugin_name=components.plugin_name,
                container=components.container,
                title=components.title,
                text=components.text,
                file=components.file,
                path_state=components.path_state,
                path_display=components.path_display,
                line_count_display=components.line_count_display,
                mode=components.mode,
                dynamic=components.dynamic,
                text_order=components.text_order,
                delimiter=components.delimiter,
                line=components.line,
                range_end=components.range_end,
                count=components.count,
                sequential_start_line=components.sequential_start_line,
                condition_type=None,  # No conditions
            )
            ui_state = gr.State()

            # Should not raise error when condition_type is None
            plugin.register_events(components_without_conditions, ui_state, event_handlers)


class TestCompleteSegmentPluginIntegration:
    """Integration tests for CompleteSegmentPlugin."""

    def test_full_workflow_no_conditions(self):
        """Test complete workflow without conditions."""
        plugin = CompleteSegmentPlugin()

        with gr.Blocks():
            # Create UI
            components = plugin.create_ui("0", ["test.txt"])

            # Get inputs
            inputs = plugin.get_input_components(components)
            assert len(inputs) == 14

            # Simulate values from UI
            values = (
                "my text",
                "",
                "test.txt",
                "Random Line",
                1,
                1,
                1,
                False,
                1,
                "text_first",
                "Space ( )",
                "None",
                "",
                False,
            )

            # Convert to config
            config = plugin.values_to_config(*values)

            assert config.text == "my text"
            assert config.file == "test.txt"
            assert config.condition_type == "None"

    def test_full_workflow_with_conditions(self):
        """Test complete workflow with character conditions."""
        plugin = CompleteSegmentPlugin()

        with gr.Blocks():
            # Create UI
            components = plugin.create_ui("0", [])

            # Get inputs
            inputs = plugin.get_input_components(components)

            # Simulate values from UI with conditions
            values = (
                "a wizard",
                "styles",
                "fantasy.txt",
                "Specific Line",
                3,
                3,
                1,
                False,
                1,
                "text_first",
                "Comma-Space (, )",
                "Character",
                "frail, modest, ancient",
                True,
            )

            # Convert to config
            config = plugin.values_to_config(*values)

            assert config.text == "a wizard"
            assert config.file == "fantasy.txt"
            assert config.line == 3
            assert config.condition_type == "Character"
            assert config.condition_text == "frail, modest, ancient"
            assert config.condition_dynamic is True

    def test_multiple_segments_independent(self):
        """Test multiple segments are independent."""
        plugin = CompleteSegmentPlugin()

        with gr.Blocks():
            comp1 = plugin.create_ui("0", [])
            comp2 = plugin.create_ui("1", [])

            # Components should be independent
            assert comp1.segment_id != comp2.segment_id
            assert comp1.text is not comp2.text
            assert comp1.file is not comp2.file
