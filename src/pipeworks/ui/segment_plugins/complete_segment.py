"""Complete segment plugin with all features: text + files + conditions.

This plugin provides a full-featured prompt segment with:
- Manual text input
- Hierarchical file browser with multiple selection modes
- Character condition generation (physique, wealth, health, demeanor, age)
- Facial condition generation (facial signals)
- Dynamic rebuild options for both segments and conditions

This is based on the current ConditionSegmentUI class and provides
the "unified" segment experience where all segments have identical capabilities.
"""

import logging

import gradio as gr

from ..models import (
    CONDITION_TYPES,
    DEFAULT_DELIMITER_LABEL,
    DELIMITER_OPTIONS,
    SEGMENT_MODES,
    TEXT_ORDER_OPTIONS,
    SegmentConfig,
)
from .base import SegmentPluginBase, SegmentUIComponents, segment_plugin_registry

logger = logging.getLogger(__name__)


class CompleteSegmentPlugin(SegmentPluginBase):
    """Complete segment with text, file browser, and condition generation.

    This plugin creates a full-featured segment that includes:
    - Text input for manual prompt text
    - Hierarchical file browser for selecting prompt files
    - Multiple selection modes (Random Line, Specific Line, Line Range, etc.)
    - Character condition generation (procedural character attributes)
    - Facial condition generation (facial signal generation)
    - Dynamic options for rebuilding content per image
    - Delimiter and text ordering controls

    The plugin mirrors the functionality of ConditionSegmentUI but uses
    the plugin architecture for better extensibility.

    Examples
    --------
    Create a complete segment:

        >>> plugin = CompleteSegmentPlugin()
        >>> with gr.Blocks():
        ...     components = plugin.create_ui("0", ["test.txt", "styles.txt"])
        ...     inputs = plugin.get_input_components(components)
        ...     # Returns 14 components

    Convert UI values to config:

        >>> values = ("my text", "", "file.txt", "Random Line", 1, 1, 1,
        ...          False, 1, "text_first", "Space ( )",
        ...          "Character", "wiry, poor", False)
        >>> config = plugin.values_to_config(*values)
        >>> print(config.text)
        'my text'
        >>> print(config.condition_type)
        'Character'
    """

    name = "Complete Segment"
    description = "Full-featured segment with text, file browser, and condition generation"
    version = "1.0.0"

    def create_ui(self, segment_id: str, initial_choices: list[str]) -> SegmentUIComponents:
        """Create UI components for a complete segment.

        This method creates all Gradio components needed for a full-featured
        segment, including condition generation controls.

        Args:
            segment_id: Unique identifier (e.g., "0", "1", "2")
            initial_choices: File browser initial choices (files/folders)

        Returns:
            SegmentUIComponents with all components populated

        Notes:
            - Creates 14 input components (11 standard + 3 condition)
            - Condition controls are initially hidden
            - All components are wrapped in a gr.Group for container management
        """
        with gr.Group() as container:
            # Title with status indicator (updated via event handlers)
            title = gr.Markdown(f"**Segment {segment_id}**")

            # ================================================================
            # CONDITION GENERATION CONTROLS (above text input)
            # ================================================================
            with gr.Group():
                gr.Markdown("**Condition Generator**")

                # Dropdown to select condition type
                condition_type = gr.Dropdown(
                    label="Condition Type",
                    choices=CONDITION_TYPES,
                    value="None",
                    info="Select type of conditions to generate",
                )

                # Condition controls (hidden until type is selected)
                with gr.Row(visible=False) as condition_controls:
                    condition_text = gr.Textbox(
                        label="Generated Condition",
                        placeholder="Select condition type to generate...",
                        lines=1,
                        interactive=True,
                        info="Edit generated text or leave blank",
                        scale=2,
                    )

                    condition_regenerate = gr.Button(
                        "🎲 Regenerate",
                        size="sm",
                        scale=1,
                        variant="secondary",
                    )

                    condition_dynamic = gr.Checkbox(
                        label="Dynamic",
                        value=False,
                        info="New condition per run",
                        scale=1,
                    )

            # ================================================================
            # STANDARD SEGMENT CONTROLS
            # ================================================================

            # Text input for manual text entry
            text = gr.Textbox(
                label=f"Segment {segment_id} Text",
                placeholder="Optional text...",
                lines=1,
            )

            # Current path display (shows where user is in folder hierarchy)
            path_display = gr.Textbox(
                label="Current Path",
                value="/inputs",
                interactive=False,
            )

            # File/folder browser dropdown
            file = gr.Dropdown(
                label="File/Folder Browser",
                choices=initial_choices,
                value="(None)",
            )

            # Line count display (shown when a file is selected)
            line_count_display = gr.Markdown(value="", visible=False)

            # Hidden state to track current navigation path
            path_state = gr.State(value="")

            # Mode and dynamic options
            with gr.Row():
                mode = gr.Dropdown(
                    label="Mode",
                    choices=SEGMENT_MODES,
                    value="Random Line",
                )
                dynamic = gr.Checkbox(
                    label="Dynamic",
                    value=False,
                    info="Rebuild this segment for each image",
                )

            # Text order and delimiter controls
            with gr.Row():
                text_order = gr.Radio(
                    label="Text Order",
                    choices=TEXT_ORDER_OPTIONS,
                    value="text_first",
                    info="Text before or after file content",
                )
                delimiter = gr.Dropdown(
                    label="Delimiter",
                    choices=DELIMITER_OPTIONS,
                    value=DEFAULT_DELIMITER_LABEL,
                    info="How to join text and file",
                )

            # Mode-specific inputs (visibility controlled by mode selection)
            with gr.Row():
                line = gr.Number(
                    label="Line #",
                    value=1,
                    minimum=1,
                    precision=0,
                    visible=False,
                )
                range_end = gr.Number(
                    label="End Line #",
                    value=1,
                    minimum=1,
                    precision=0,
                    visible=False,
                )
                count = gr.Number(
                    label="Count",
                    value=1,
                    minimum=1,
                    maximum=10,
                    precision=0,
                    visible=False,
                )
                sequential_start_line = gr.Number(
                    label="Start Line #",
                    value=1,
                    minimum=1,
                    precision=0,
                    visible=False,
                    info="Starting line for sequential mode",
                )

        return SegmentUIComponents(
            segment_id=segment_id,
            plugin_name=self.name,
            container=container,
            title=title,
            text=text,
            file=file,
            path_state=path_state,
            path_display=path_display,
            line_count_display=line_count_display,
            mode=mode,
            dynamic=dynamic,
            text_order=text_order,
            delimiter=delimiter,
            line=line,
            range_end=range_end,
            count=count,
            sequential_start_line=sequential_start_line,
            condition_type=condition_type,
            condition_text=condition_text,
            condition_regenerate=condition_regenerate,
            condition_dynamic=condition_dynamic,
            condition_controls=condition_controls,
        )

    def get_input_components(self, components: SegmentUIComponents) -> list[gr.Component]:
        """Return components used as function inputs.

        This method returns all 14 input components in the order expected
        by event handlers and values_to_config().

        Args:
            components: SegmentUIComponents created by create_ui()

        Returns:
            List of 14 Gradio components in fixed order:
                [text, path_state, file, mode, line, range_end, count, dynamic,
                 sequential_start_line, text_order, delimiter,
                 condition_type, condition_text, condition_dynamic]

        Notes:
            - Order must match values_to_config() parameter order
            - Includes both standard (11) and condition (3) components
        """
        # Type assertions for condition components (they're always present in CompleteSegment)
        assert components.condition_type is not None
        assert components.condition_text is not None
        assert components.condition_dynamic is not None

        return [
            components.text,
            components.path_state,
            components.file,
            components.mode,
            components.line,
            components.range_end,
            components.count,
            components.dynamic,
            components.sequential_start_line,
            components.text_order,
            components.delimiter,
            components.condition_type,
            components.condition_text,
            components.condition_dynamic,
        ]

    def values_to_config(self, *values) -> SegmentConfig:
        """Convert UI values to SegmentConfig.

        This method takes 14 values from get_input_components() and converts
        them to a properly typed SegmentConfig dataclass instance.

        Args:
            *values: 14 values in order:
                text (str), path_state (str), file (str), mode (str),
                line (int), range_end (int), count (int), dynamic (bool),
                sequential_start_line (int), text_order (str), delimiter (str),
                condition_type (str), condition_text (str), condition_dynamic (bool)

        Returns:
            SegmentConfig instance with all fields populated

        Raises:
            ValueError: If incorrect number of values provided
            TypeError: If value types are incorrect

        Examples:
            >>> plugin = CompleteSegmentPlugin()
            >>> values = ("text", "", "file.txt", "Random Line", 1, 1, 1,
            ...          False, 1, "text_first", "Space ( )",
            ...          "None", "", False)
            >>> config = plugin.values_to_config(*values)
            >>> config.text
            'text'
            >>> config.file
            'file.txt'

        Notes:
            - Number values are converted to int with default of 1 if missing
            - Empty strings are preserved (not converted to defaults)
            - Boolean values must be actual bool (not strings)
        """
        if len(values) != 14:
            raise ValueError(f"Expected 14 values for CompleteSegmentPlugin, got {len(values)}")

        # Unpack values in order
        (
            text,
            path_state,
            file,
            mode,
            line,
            range_end,
            count,
            dynamic,
            sequential_start_line,
            text_order,
            delimiter,
            condition_type,
            condition_text,
            condition_dynamic,
        ) = values

        # Convert to SegmentConfig with proper type conversions
        return SegmentConfig(
            text=text,
            path=path_state,
            file=file,
            mode=mode,
            line=int(line) if line else 1,
            range_end=int(range_end) if range_end else 1,
            count=int(count) if count else 1,
            dynamic=dynamic,
            sequential_start_line=int(sequential_start_line) if sequential_start_line else 1,
            text_order=text_order,
            delimiter=delimiter,
            condition_type=condition_type,
            condition_text=condition_text,
            condition_dynamic=condition_dynamic,
        )

    def register_events(
        self,
        components: SegmentUIComponents,
        ui_state: gr.State,
        event_handlers: dict,
    ) -> None:
        """Register event handlers for this segment.

        This method wires up all event handlers for file navigation,
        mode visibility changes, and condition generation.

        Args:
            components: SegmentUIComponents created by create_ui()
            ui_state: Global UI state (gr.State)
            event_handlers: Dict of handler functions with keys:
                - "navigate_file_selection": File browser navigation handler
                - "update_mode_visibility": Mode-specific input visibility handler
                - "toggle_condition_type": Condition type selection handler
                - "regenerate_condition": Condition regeneration handler

        Returns:
            None (events are registered as side effects)

        Notes:
            - File navigation uses .change() event chained with .then()
            - Mode visibility is updated on mode dropdown change
            - Condition events only registered if condition_type is not None
            - All handlers must be provided in event_handlers dict

        Raises:
            KeyError: If required handler is missing from event_handlers
        """
        # ================================================================
        # FILE BROWSER NAVIGATION
        # ================================================================
        components.file.change(
            fn=event_handlers["navigate_file_selection"],
            inputs=[components.file, components.path_state, ui_state],
            outputs=[
                components.file,
                components.path_state,
                components.line_count_display,
                ui_state,
            ],
        ).then(
            # Update path display based on current path state
            fn=lambda path: f"/inputs/{path}" if path else "/inputs",
            inputs=[components.path_state],
            outputs=[components.path_display],
        )

        # ================================================================
        # MODE VISIBILITY UPDATES
        # ================================================================
        components.mode.change(
            fn=event_handlers["update_mode_visibility"],
            inputs=[components.mode],
            outputs=[
                components.line,
                components.range_end,
                components.count,
                components.sequential_start_line,
            ],
        )

        # ================================================================
        # CONDITION GENERATION (if supported)
        # ================================================================
        if components.condition_type is not None:
            # Type assertions for mypy (these should always be present together)
            assert components.condition_text is not None
            assert components.condition_controls is not None
            assert components.condition_regenerate is not None

            # Toggle condition controls visibility when type changes
            components.condition_type.change(
                fn=event_handlers["toggle_condition_type"],
                inputs=[components.condition_type],
                outputs=[components.condition_text, components.condition_controls],
            )

            # Regenerate condition when button clicked
            components.condition_regenerate.click(
                fn=event_handlers["regenerate_condition"],
                inputs=[components.condition_type],
                outputs=[components.condition_text],
            )


# Register plugin in the global registry
segment_plugin_registry.register(CompleteSegmentPlugin)
