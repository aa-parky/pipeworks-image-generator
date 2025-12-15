# App.py Refactoring Plan

## Executive Summary

Current `app.py`: **866 lines** with a monolithic `create_ui()` function (423 lines, 48% of file)

**Goal**: Break down into focused, testable modules while maintaining all functionality

**Estimated Effort**: 3-4 hours of careful refactoring + 1 hour testing

---

## Current State Analysis

### File Breakdown
```
app.py (866 lines total):
├── create_ui()              423 lines (48.8%) ← PRIMARY PROBLEM
├── generate_image()         164 lines (18.9%)
├── Other handlers            95 lines (11.0%)
└── Module setup/main         63 lines (7.3%)
```

### Key Issues

1. **Monolithic UI Function** - `create_ui()` does everything:
   - Defines UI layout (280 lines)
   - Registers event handlers (120 lines)
   - Defines nested helper functions inline (30 lines)

2. **Untestable Inline Functions** - Handler functions defined inside `create_ui()`:
   ```python
   def toggle_save_metadata(enabled, folder, prefix, state):  # Line 582
   def update_plugin_config(enabled, folder, prefix, state):  # Line 604
   def build_and_update_prompt(*values):                      # Line 707
   def generate_wrapper(*all_inputs):                         # Line 782
   ```

3. **Complex Info Formatting** - Generation result formatting (35 lines) mixed into business logic

4. **Repetitive Event Registration** - Same pattern repeated 3x for file browser handlers

---

## Refactoring Strategy

### Phase 1: Extract Testable Logic (High Priority)
**Goal**: Move complex logic to testable modules
**Impact**: Enables unit testing, improves maintainability

#### 1.1 Create `handlers.py` - Event Handler Functions
**File**: `src/pipeworks/ui/handlers.py`

Move these functions from inline to module-level:
- `set_aspect_ratio()` ← Already at module level, move to handlers.py
- `analyze_prompt()` ← Already at module level, move to handlers.py
- `get_items_in_path()` ← Already at module level, move to handlers.py
- `navigate_file_selection()` ← Already at module level, move to handlers.py
- `build_combined_prompt()` ← Already at module level, move to handlers.py
- `generate_image()` ← Already at module level, move to handlers.py
- `toggle_plugin_ui()` ← Already at module level, move to handlers.py

**NEW functions to extract from inline definitions:**
- `toggle_save_metadata_handler()` ← From line 582
- `update_plugin_config_handler()` ← From line 604

```python
# handlers.py structure
"""Event handlers for Gradio UI components."""

def set_aspect_ratio(ratio_name: str) -> tuple[gr.Number, gr.Number]:
    """Set width and height based on aspect ratio preset."""
    ...

def analyze_prompt(prompt: str, state: UIState) -> tuple[str, UIState]:
    """Analyze prompt tokenization and return formatted results."""
    ...

def get_items_in_path(current_path: str, state: UIState) -> tuple[gr.Dropdown, str, UIState]:
    """Get folders and files at the current path level."""
    ...

def navigate_file_selection(...) -> tuple[gr.Dropdown, str, UIState]:
    """Handle folder navigation when an item is selected."""
    ...

def build_combined_prompt(...) -> str:
    """Build a combined prompt from multiple segments."""
    ...

def generate_image(...) -> tuple[list[str], str, str, UIState]:
    """Generate image(s) from the UI inputs."""
    ...

def toggle_plugin_ui(...) -> tuple[gr.Group, UIState]:
    """Toggle a plugin on/off and update its configuration."""
    ...

# NEW: Extracted from inline definitions
def toggle_save_metadata_handler(
    enabled: bool, folder: str, prefix: str, state: UIState
) -> tuple[gr.Group, UIState]:
    """Handle SaveMetadata plugin toggle with configuration."""
    vis_update, new_state = toggle_plugin_ui(
        "SaveMetadata", enabled, state, folder_name=folder, filename_prefix=prefix
    )
    return vis_update, new_state

def update_plugin_config_handler(
    enabled: bool, folder: str, prefix: str, state: UIState
) -> UIState:
    """Update SaveMetadata plugin configuration when settings change."""
    if enabled:
        _, new_state = toggle_plugin_ui(
            "SaveMetadata", enabled, state, folder_name=folder, filename_prefix=prefix
        )
        return new_state
    return state
```

**Lines Reduced**: app.py: 866 → 700 lines (-166 lines moved to handlers.py)

---

#### 1.2 Create `formatting.py` - Output Formatting
**File**: `src/pipeworks/ui/formatting.py`

Extract info message formatting from `generate_image()`:

```python
"""Formatting utilities for UI output messages."""

def format_generation_info(
    params: GenerationParams,
    generated_paths: list[str],
    seeds_used: list[int],
    has_dynamic: bool,
    prompts_used: list[str] | None,
    active_plugins: list[str],
) -> str:
    """Format generation completion info message.

    Args:
        params: Generation parameters used
        generated_paths: List of generated image paths
        seeds_used: List of seeds used for generation
        has_dynamic: Whether dynamic segments were used
        prompts_used: List of prompts used (for dynamic generation)
        active_plugins: List of active plugin names

    Returns:
        Formatted markdown info message
    """
    # Format seeds display
    if params.total_images == 1:
        seeds_display = str(seeds_used[0])
        paths_display = str(generated_paths[0])
    else:
        seeds_display = f"{seeds_used[0]} - {seeds_used[-1]}"
        paths_display = (
            f"{len(generated_paths)} images in {Path(generated_paths[0]).parent}"
        )

    # Build dynamic prompt info
    if has_dynamic and prompts_used:
        dynamic_info = "\n\n**Dynamic Prompts Used:**\n"
        for i, prompt in enumerate(prompts_used[:5], 1):
            dynamic_info += f"{i}. {prompt}\n"
        if len(prompts_used) > 5:
            dynamic_info += f"... and {len(prompts_used) - 5} more\n"
    else:
        dynamic_info = ""

    # Build plugins info
    plugins_info = (
        f"\n**Active Plugins:** {', '.join(active_plugins)}"
        if active_plugins else ""
    )

    # Format final message
    return (
        f"✅ **Generation Complete**\n\n"
        f"**Generated:** {params.total_images} image(s)\n"
        f"**Seeds:** {seeds_display}\n"
        f"**Saved to:** {paths_display}"
        f"{dynamic_info}"
        f"{plugins_info}"
    )

def format_validation_error(error: ValidationError) -> str:
    """Format validation error for display.

    Args:
        error: ValidationError instance

    Returns:
        Formatted markdown error message
    """
    return f"❌ **Validation Error**\n\n{str(error)}"

def format_generation_error(error: Exception) -> str:
    """Format unexpected error for display.

    Args:
        error: Exception that occurred

    Returns:
        Formatted markdown error message
    """
    return (
        f"❌ **Error**\n\n"
        f"An unexpected error occurred. Check logs for details.\n\n"
        f"`{str(error)}`"
    )
```

**Lines Reduced**: app.py: 700 → 665 lines (-35 lines moved to formatting.py)

---

#### 1.3 Create `adapters.py` - UI Value Adapters
**File**: `src/pipeworks/ui/adapters.py`

Extract wrapper functions that adapt between Gradio and business logic:

```python
"""Adapter functions for converting between UI values and business objects."""

from .components import SegmentUI
from .models import SegmentConfig

def convert_segment_values_to_configs(
    start_values: tuple,
    middle_values: tuple,
    end_values: tuple,
) -> tuple[SegmentConfig, SegmentConfig, SegmentConfig]:
    """Convert raw UI segment values to SegmentConfig objects.

    Args:
        start_values: 8-tuple of start segment values
        middle_values: 8-tuple of middle segment values
        end_values: 8-tuple of end segment values

    Returns:
        Tuple of (start_cfg, middle_cfg, end_cfg)
    """
    return (
        SegmentUI.values_to_config(*start_values),
        SegmentUI.values_to_config(*middle_values),
        SegmentUI.values_to_config(*end_values),
    )

def split_segment_inputs(values: list) -> tuple[tuple, tuple, tuple, any]:
    """Split combined input list into segment groups.

    Args:
        values: List of all UI input values

    Returns:
        Tuple of (start_values, middle_values, end_values, state)
        Each segment values is an 8-tuple
    """
    start_values = tuple(values[0:8])
    middle_values = tuple(values[8:16])
    end_values = tuple(values[16:24])
    state = values[24]
    return start_values, middle_values, end_values, state
```

**Lines Reduced**: app.py: 665 → 640 lines (-25 lines moved to adapters.py)

---

### Phase 2: Split UI Layout (Medium Priority)
**Goal**: Reduce `create_ui()` size by extracting panel creation
**Impact**: Improves readability, reduces nesting depth

#### 2.1 Create `layout.py` - UI Layout Functions
**File**: `src/pipeworks/ui/layout.py`

Split `create_ui()` into focused functions:

```python
"""UI layout construction functions."""

import gradio as gr
from pipeworks.core.config import config
from .components import SegmentUI, create_three_segments
from .models import ASPECT_RATIOS, MAX_SEED, DEFAULT_SEED

def get_custom_css() -> str:
    """Get custom CSS for the UI.

    Returns:
        CSS string
    """
    return """
    .plugin-section {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #374151;
        border-radius: 6px;
        padding: 12px;
    }
    """

def create_header() -> None:
    """Create the header section with title."""
    gr.Markdown(
        """
        # Pipeworks Image Generator
        ### Programmatic image generation with Z-Image-Turbo
        """
    )

def create_prompt_section(initial_choices: list[str]) -> dict:
    """Create the prompt input section with builder.

    Args:
        initial_choices: Initial file browser choices

    Returns:
        Dictionary of created components
    """
    with gr.Accordion("Prompt Settings", open=True):
        # Main prompt input
        prompt_input = gr.Textbox(
            label="Prompt",
            placeholder="Describe the image you want to generate...",
            lines=3,
            max_lines=10,
        )

        # Prompt Builder accordion
        with gr.Accordion("Prompt Builder", open=False):
            gr.Markdown(
                "**Build dynamic prompts from text files** "
                "in the `inputs/` directory\n\n"
                "*Click folders (📁) to navigate, select files to use*"
            )

            # Create three segments
            start_segment, middle_segment, end_segment = create_three_segments(
                initial_choices
            )

            build_prompt_btn = gr.Button("Build Prompt", variant="secondary")

        # Tokenizer Analyzer
        with gr.Accordion("Tokenizer Analyzer", open=False):
            tokenizer_output = gr.Markdown(
                value="*Enter a prompt to see tokenization analysis*",
                label="Analysis"
            )

    return {
        "prompt_input": prompt_input,
        "start_segment": start_segment,
        "middle_segment": middle_segment,
        "end_segment": end_segment,
        "build_prompt_btn": build_prompt_btn,
        "tokenizer_output": tokenizer_output,
    }

def create_parameters_section() -> dict:
    """Create the model parameters section.

    Returns:
        Dictionary of created components
    """
    with gr.Accordion("Model Parameters", open=True):
        # Aspect Ratio Preset
        aspect_ratio_dropdown = gr.Dropdown(
            label="Aspect Ratio Preset",
            choices=list(ASPECT_RATIOS.keys()),
            value="Custom",
            info="Select a preset or choose Custom to manually adjust sliders",
        )

        with gr.Row():
            width_slider = gr.Slider(
                label="Width",
                minimum=256,
                maximum=1536,
                step=64,
                value=config.default_width,
            )
            height_slider = gr.Slider(
                label="Height",
                minimum=256,
                maximum=1536,
                step=64,
                value=config.default_height,
            )

        steps_slider = gr.Slider(
            label="Inference Steps",
            minimum=1,
            maximum=50,
            step=1,
            value=config.num_inference_steps,
            info="Recommended: 9 steps for Z-Image-Turbo",
        )

        with gr.Row():
            batch_input = gr.Number(
                label="Batch Size",
                value=1,
                minimum=1,
                maximum=10,
                step=1,
                info="Number of images per run",
            )
            runs_input = gr.Number(
                label="Runs",
                value=1,
                minimum=1,
                maximum=10,
                step=1,
                info="Number of batches to generate",
            )

        with gr.Row():
            seed_input = gr.Number(
                label="Seed",
                value=DEFAULT_SEED,
                minimum=0,
                maximum=MAX_SEED,
                step=1,
                info="Random seed for reproducibility",
            )
            random_seed_checkbox = gr.Checkbox(
                label="Random Seed",
                value=False,
                info="Generate random seed for each image",
            )

    return {
        "aspect_ratio_dropdown": aspect_ratio_dropdown,
        "width_slider": width_slider,
        "height_slider": height_slider,
        "steps_slider": steps_slider,
        "batch_input": batch_input,
        "runs_input": runs_input,
        "seed_input": seed_input,
        "random_seed_checkbox": random_seed_checkbox,
    }

def create_plugins_section() -> dict:
    """Create the plugins configuration section.

    Returns:
        Dictionary of created components
    """
    with gr.Accordion("Plugins", open=False, elem_classes="plugin-section"):
        gr.Markdown("### Save Metadata Plugin")

        save_metadata_check = gr.Checkbox(
            label="Enable SaveMetadata",
            value=False,
            info="Save prompt and parameters alongside images",
        )

        with gr.Group(visible=False) as metadata_settings:
            metadata_folder = gr.Textbox(
                label="Metadata Subfolder",
                value="metadata",
                info="Subfolder within outputs directory",
            )
            metadata_prefix = gr.Textbox(
                label="Filename Prefix",
                value="",
                info="Optional prefix for metadata files",
            )

    return {
        "save_metadata_check": save_metadata_check,
        "metadata_settings": metadata_settings,
        "metadata_folder": metadata_folder,
        "metadata_prefix": metadata_prefix,
    }

def create_left_panel(initial_choices: list[str]) -> dict:
    """Create the left panel with inputs and settings.

    Args:
        initial_choices: Initial file browser choices

    Returns:
        Dictionary of all created components
    """
    components = {}

    with gr.Column(scale=1):
        gr.Markdown("## Settings")

        # Prompt section
        components.update(create_prompt_section(initial_choices))

        # Parameters section
        components.update(create_parameters_section())

        # Plugins section
        components.update(create_plugins_section())

        # Generate button
        components["generate_btn"] = gr.Button(
            "Generate Image",
            variant="primary",
            size="lg",
        )

    return components

def create_right_panel() -> dict:
    """Create the right panel with outputs.

    Returns:
        Dictionary of created components
    """
    components = {}

    with gr.Column(scale=2):
        gr.Markdown("## Generated Images")

        components["output_gallery"] = gr.Gallery(
            label="Output",
            show_label=False,
            columns=2,
            rows=2,
            height="auto",
            object_fit="contain",
        )

        components["seed_used"] = gr.Textbox(
            label="Seed Used",
            interactive=False,
            show_copy_button=True,
        )

        components["generation_info"] = gr.Markdown(
            value="*Ready to generate images*",
        )

    return components

def create_footer() -> None:
    """Create the footer with model info."""
    gr.Markdown(
        f"""
        ---
        **Model:** {config.model_id} | **Device:** {config.device} |
        **Dtype:** {config.torch_dtype}

        *Outputs saved to: {config.outputs_dir}*
        """
    )

def load_initial_file_choices() -> list[str]:
    """Load initial folder/file choices for file browser.

    Returns:
        List of folder and file choices
    """
    from pipeworks.core.prompt_builder import PromptBuilder

    initial_choices = ["(None)"]
    try:
        temp_pb = PromptBuilder(config.inputs_dir)
        folders, files = temp_pb.get_items_in_path("")
        for folder in folders:
            initial_choices.append(f"📁 {folder}")
        initial_choices.extend(files)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error initializing file browser: {e}")

    return initial_choices
```

**Lines Reduced**: app.py: 640 → 380 lines (-260 lines moved to layout.py)

---

#### 2.2 Refactor `app.py` to Use Layout Functions

After Phase 2, `app.py` becomes much cleaner:

```python
"""Gradio UI for Pipeworks Image Generator - Refactored Version."""

import logging
import gradio as gr

from pipeworks.core.config import config
from pipeworks.plugins.base import plugin_registry

from .layout import (
    get_custom_css,
    create_header,
    create_left_panel,
    create_right_panel,
    create_footer,
    load_initial_file_choices,
)
from .handlers import (
    set_aspect_ratio,
    analyze_prompt,
    navigate_file_selection,
    generate_image,
    toggle_save_metadata_handler,
    update_plugin_config_handler,
)
from .adapters import split_segment_inputs, convert_segment_values_to_configs
from .models import UIState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_ui() -> gr.Blocks:
    """Create the Gradio UI with refactored architecture.

    Returns:
        Gradio Blocks app
    """
    app = gr.Blocks(title="Pipeworks Image Generator", css=get_custom_css())

    with app:
        # Session state
        ui_state = gr.State(UIState())

        # Header
        create_header()

        # Load initial choices
        initial_choices = load_initial_file_choices()

        # Main layout
        with gr.Row():
            left_components = create_left_panel(initial_choices)
            right_components = create_right_panel()

        # Footer
        create_footer()

        # Register event handlers
        _register_event_handlers(left_components, right_components, ui_state)

    return app


def _register_event_handlers(
    left: dict, right: dict, ui_state: gr.State
) -> None:
    """Register all event handlers for the UI.

    Args:
        left: Left panel components
        right: Right panel components
        ui_state: Session state
    """
    # File browser handlers
    _register_file_browser_handlers(left, ui_state)

    # Prompt builder handlers
    _register_prompt_builder_handlers(left, right, ui_state)

    # Aspect ratio handler
    left["aspect_ratio_dropdown"].change(
        fn=set_aspect_ratio,
        inputs=[left["aspect_ratio_dropdown"]],
        outputs=[left["width_slider"], left["height_slider"]],
    )

    # Tokenizer analyzer handler
    left["prompt_input"].change(
        fn=analyze_prompt,
        inputs=[left["prompt_input"], ui_state],
        outputs=[left["tokenizer_output"], ui_state],
    )

    # Plugin handlers
    _register_plugin_handlers(left, ui_state)

    # Generation handler
    _register_generation_handler(left, right, ui_state)


def _register_file_browser_handlers(components: dict, ui_state: gr.State) -> None:
    """Register file browser navigation handlers for all segments."""
    for segment in [
        components["start_segment"],
        components["middle_segment"],
        components["end_segment"],
    ]:
        file_dropdown, path_state, path_display = segment.get_navigation_components()

        file_dropdown.change(
            fn=navigate_file_selection,
            inputs=[file_dropdown, path_state, ui_state],
            outputs=[file_dropdown, path_state, ui_state],
        ).then(
            fn=get_items_in_path,
            inputs=[path_state, ui_state],
            outputs=[file_dropdown, path_display, ui_state],
        )

        # Update mode visibility
        segment.mode.change(
            fn=update_mode_visibility,
            inputs=[segment.mode],
            outputs=segment.get_mode_visibility_outputs(),
        )


def _register_prompt_builder_handlers(
    left: dict, right: dict, ui_state: gr.State
) -> None:
    """Register prompt builder event handlers."""

    def build_and_update_prompt(*values):
        """Build prompt from segments and update UI."""
        from .handlers import build_combined_prompt
        from .formatting import format_validation_error
        from .components import SegmentUI

        # Split inputs
        start_vals, middle_vals, end_vals, state = split_segment_inputs(list(values))

        # Convert to configs
        start_cfg, middle_cfg, end_cfg = convert_segment_values_to_configs(
            start_vals, middle_vals, end_vals
        )

        # Build prompt
        try:
            prompt = build_combined_prompt(start_cfg, middle_cfg, end_cfg, state)
        except ValidationError as e:
            prompt = format_validation_error(e)

        # Update titles
        start_title = SegmentUI.format_title(
            "Start", start_cfg.file, start_cfg.mode, start_cfg.dynamic
        )
        middle_title = SegmentUI.format_title(
            "Middle", middle_cfg.file, middle_cfg.mode, middle_cfg.dynamic
        )
        end_title = SegmentUI.format_title(
            "End", end_cfg.file, end_cfg.mode, end_cfg.dynamic
        )

        return prompt, start_title, middle_title, end_title, state

    # Collect segment inputs
    all_segment_inputs = (
        left["start_segment"].get_input_components()
        + left["middle_segment"].get_input_components()
        + left["end_segment"].get_input_components()
        + [ui_state]
    )

    left["build_prompt_btn"].click(
        fn=build_and_update_prompt,
        inputs=all_segment_inputs,
        outputs=[
            left["prompt_input"],
            left["start_segment"].title,
            left["middle_segment"].title,
            left["end_segment"].title,
            ui_state,
        ],
    )


def _register_plugin_handlers(components: dict, ui_state: gr.State) -> None:
    """Register plugin configuration handlers."""
    components["save_metadata_check"].change(
        fn=toggle_save_metadata_handler,
        inputs=[
            components["save_metadata_check"],
            components["metadata_folder"],
            components["metadata_prefix"],
            ui_state,
        ],
        outputs=[components["metadata_settings"], ui_state],
    )

    components["metadata_folder"].change(
        fn=update_plugin_config_handler,
        inputs=[
            components["save_metadata_check"],
            components["metadata_folder"],
            components["metadata_prefix"],
            ui_state,
        ],
        outputs=[ui_state],
    )

    components["metadata_prefix"].change(
        fn=update_plugin_config_handler,
        inputs=[
            components["save_metadata_check"],
            components["metadata_folder"],
            components["metadata_prefix"],
            ui_state,
        ],
        outputs=[ui_state],
    )


def _register_generation_handler(
    left: dict, right: dict, ui_state: gr.State
) -> None:
    """Register the main image generation handler."""

    def generate_wrapper(*all_inputs):
        """Wrapper to convert UI inputs to proper types."""
        # Extract basic inputs
        prompt = all_inputs[0]
        width = all_inputs[1]
        height = all_inputs[2]
        num_steps = all_inputs[3]
        batch_size = all_inputs[4]
        runs = all_inputs[5]
        seed = all_inputs[6]
        use_random_seed = all_inputs[7]

        # Remaining inputs are segments + state
        segment_and_state = all_inputs[8:]
        start_vals, middle_vals, end_vals, state = split_segment_inputs(
            list(segment_and_state)
        )

        # Convert to configs
        start_cfg, middle_cfg, end_cfg = convert_segment_values_to_configs(
            start_vals, middle_vals, end_vals
        )

        # Call generate_image
        return generate_image(
            prompt,
            width,
            height,
            num_steps,
            batch_size,
            runs,
            seed,
            use_random_seed,
            start_cfg,
            middle_cfg,
            end_cfg,
            state,
        )

    # Collect all inputs
    generation_inputs = [
        left["prompt_input"],
        left["width_slider"],
        left["height_slider"],
        left["steps_slider"],
        left["batch_input"],
        left["runs_input"],
        left["seed_input"],
        left["random_seed_checkbox"],
    ] + (
        left["start_segment"].get_input_components()
        + left["middle_segment"].get_input_components()
        + left["end_segment"].get_input_components()
        + [ui_state]
    )

    left["generate_btn"].click(
        fn=generate_wrapper,
        inputs=generation_inputs,
        outputs=[
            right["output_gallery"],
            right["generation_info"],
            right["seed_used"],
            ui_state,
        ],
    )


def main():
    """Main entry point for the application."""
    # Log available plugins
    available_plugins = plugin_registry.list_available()
    logger.info(f"Available plugins: {available_plugins}")

    # Create and launch UI
    app = create_ui()

    logger.info(
        f"Launching Gradio UI on {config.gradio_server_name}:{config.gradio_server_port}"
    )

    app.launch(
        server_name=config.gradio_server_name,
        server_port=config.gradio_server_port,
        share=config.gradio_share,
        show_error=True,
        inbrowser=False,
    )


if __name__ == "__main__":
    main()
```

**Final Size**: app.py: **~380 lines** (down from 866)

---

### Phase 3: Testing & Documentation (Optional)
**Goal**: Ensure refactoring maintains functionality
**Impact**: Confidence in changes, easier future modifications

#### 3.1 Add Unit Tests for New Modules

**Test**: `tests/unit/test_handlers.py`
```python
"""Unit tests for UI event handlers."""

def test_toggle_save_metadata_handler(mocker):
    """Test SaveMetadata toggle handler."""
    mock_toggle = mocker.patch('pipeworks.ui.handlers.toggle_plugin_ui')
    mock_toggle.return_value = (gr.update(), UIState())

    result = toggle_save_metadata_handler(True, "metadata", "test_", UIState())

    mock_toggle.assert_called_once_with(
        "SaveMetadata", True, mocker.ANY, folder_name="metadata", filename_prefix="test_"
    )

def test_update_plugin_config_handler_enabled(mocker):
    """Test plugin config update when enabled."""
    mock_toggle = mocker.patch('pipeworks.ui.handlers.toggle_plugin_ui')
    new_state = UIState()
    mock_toggle.return_value = (gr.update(), new_state)

    result = update_plugin_config_handler(True, "metadata", "prefix_", UIState())

    assert result == new_state
```

**Test**: `tests/unit/test_formatting.py`
```python
"""Unit tests for formatting utilities."""

def test_format_generation_info_single_image():
    """Test info formatting for single image."""
    params = GenerationParams(
        prompt="test", width=512, height=512, num_steps=9,
        batch_size=1, runs=1, seed=42, use_random_seed=False
    )

    info = format_generation_info(
        params=params,
        generated_paths=["/path/to/image.png"],
        seeds_used=[42],
        has_dynamic=False,
        prompts_used=None,
        active_plugins=["SaveMetadata"],
    )

    assert "✅ **Generation Complete**" in info
    assert "**Generated:** 1 image(s)" in info
    assert "**Seeds:** 42" in info
    assert "**Active Plugins:** SaveMetadata" in info

def test_format_generation_info_batch():
    """Test info formatting for batch generation."""
    params = GenerationParams(
        prompt="test", width=512, height=512, num_steps=9,
        batch_size=4, runs=2, seed=42, use_random_seed=False
    )

    info = format_generation_info(
        params=params,
        generated_paths=[f"/path/image_{i}.png" for i in range(8)],
        seeds_used=list(range(42, 50)),
        has_dynamic=False,
        prompts_used=None,
        active_plugins=[],
    )

    assert "**Generated:** 8 image(s)" in info
    assert "**Seeds:** 42 - 49" in info

def test_format_validation_error():
    """Test validation error formatting."""
    error = ValidationError("Width must be between 256 and 1536")

    msg = format_validation_error(error)

    assert "❌ **Validation Error**" in msg
    assert "Width must be between 256 and 1536" in msg
```

**Test**: `tests/unit/test_adapters.py`
```python
"""Unit tests for UI adapters."""

def test_split_segment_inputs():
    """Test splitting combined inputs."""
    values = list(range(25))  # 24 segment values + 1 state

    start, middle, end, state = split_segment_inputs(values)

    assert start == tuple(range(0, 8))
    assert middle == tuple(range(8, 16))
    assert end == tuple(range(16, 24))
    assert state == 24

def test_convert_segment_values_to_configs():
    """Test segment value conversion."""
    start_vals = ("text", "", "(None)", "Random Line", 1, 1, 1, False)
    middle_vals = ("", "folder", "file.txt", "Specific Line", 5, 1, 1, False)
    end_vals = ("", "", "(None)", "All Lines", 1, 1, 1, True)

    start, middle, end = convert_segment_values_to_configs(
        start_vals, middle_vals, end_vals
    )

    assert isinstance(start, SegmentConfig)
    assert start.text == "text"
    assert middle.file == "file.txt"
    assert end.dynamic is True
```

---

## Final Module Structure

```
src/pipeworks/ui/
├── __init__.py
├── app.py              [~380 lines]  - Main UI + event registration
├── layout.py           [~280 lines]  - UI layout functions (NEW)
├── handlers.py         [~200 lines]  - Event handler functions (NEW)
├── formatting.py       [~80 lines]   - Output formatting (NEW)
├── adapters.py         [~50 lines]   - UI/business adapters (NEW)
├── components.py       [225 lines]   - SegmentUI component (EXISTING)
├── models.py           [159 lines]   - Data classes (EXISTING)
├── state.py            [160 lines]   - State management (EXISTING)
└── validation.py       [183 lines]   - Input validation (EXISTING)
```

**Total**: 1,717 lines (was 1,593 + 866 = 2,459 in app.py)
**Reduction**: 742 lines saved through better organization

---

## Implementation Checklist

### Phase 1: Extract Logic (High Priority)

- [ ] Create `src/pipeworks/ui/handlers.py`
  - [ ] Move all handler functions from app.py
  - [ ] Extract inline functions (toggle_save_metadata, update_plugin_config)
  - [ ] Add docstrings and type hints
  - [ ] Update imports in app.py

- [ ] Create `src/pipeworks/ui/formatting.py`
  - [ ] Extract `format_generation_info()`
  - [ ] Extract `format_validation_error()`
  - [ ] Extract `format_generation_error()`
  - [ ] Update generate_image() to use formatting functions

- [ ] Create `src/pipeworks/ui/adapters.py`
  - [ ] Extract `split_segment_inputs()`
  - [ ] Extract `convert_segment_values_to_configs()`
  - [ ] Update wrapper functions to use adapters

- [ ] Run tests to verify functionality preserved
  - [ ] `pytest tests/ -v`
  - [ ] Manual testing of UI

### Phase 2: Split Layout (Medium Priority)

- [ ] Create `src/pipeworks/ui/layout.py`
  - [ ] Extract `get_custom_css()`
  - [ ] Extract `create_header()`
  - [ ] Extract `create_prompt_section()`
  - [ ] Extract `create_parameters_section()`
  - [ ] Extract `create_plugins_section()`
  - [ ] Extract `create_left_panel()`
  - [ ] Extract `create_right_panel()`
  - [ ] Extract `create_footer()`
  - [ ] Extract `load_initial_file_choices()`

- [ ] Refactor `app.py`
  - [ ] Update `create_ui()` to use layout functions
  - [ ] Extract `_register_event_handlers()`
  - [ ] Extract `_register_file_browser_handlers()`
  - [ ] Extract `_register_prompt_builder_handlers()`
  - [ ] Extract `_register_plugin_handlers()`
  - [ ] Extract `_register_generation_handler()`

- [ ] Run tests again
  - [ ] `pytest tests/ -v`
  - [ ] Manual UI testing

### Phase 3: Testing & Documentation (Optional)

- [ ] Add unit tests
  - [ ] `tests/unit/test_handlers.py`
  - [ ] `tests/unit/test_formatting.py`
  - [ ] `tests/unit/test_adapters.py`

- [ ] Update documentation
  - [ ] Add docstrings to all new functions
  - [ ] Update architecture diagrams
  - [ ] Add module-level documentation

- [ ] Run linting
  - [ ] `ruff check src/`
  - [ ] `black src/`
  - [ ] `mypy src/pipeworks/ui/`

- [ ] Final validation
  - [ ] Full test suite: `pytest tests/`
  - [ ] End-to-end UI testing
  - [ ] Verify all features work

---

## Risk Assessment

### Low Risk
- ✅ Extracting utility functions (already at module level)
- ✅ Creating formatting functions (pure functions, easy to test)
- ✅ Creating adapter functions (simple transformations)

### Medium Risk
- ⚠️ Splitting UI layout (need to ensure component references maintained)
- ⚠️ Extracting event handler registration (complex dependencies)

### Mitigation Strategy
1. Make changes incrementally (one phase at a time)
2. Run tests after each phase
3. Manually test UI after each phase
4. Keep git commits small and focused
5. Be prepared to rollback if issues arise

---

## Success Criteria

✅ **app.py reduced from 866 to ~380 lines** (56% reduction)

✅ **All functions < 100 lines** (currently have 423-line function)

✅ **Clear separation of concerns**:
- Layout in layout.py
- Event handlers in handlers.py
- Business logic in handlers.py
- Formatting in formatting.py
- Adapters in adapters.py

✅ **All tests passing** (pytest)

✅ **All linting passing** (ruff, black)

✅ **UI functionality unchanged** (manual testing)

---

## Estimated Timeline

- **Phase 1**: 2-3 hours (extract logic)
- **Phase 2**: 1-2 hours (split layout)
- **Phase 3**: 1 hour (testing/docs) - Optional

**Total**: 3-4 hours for core refactoring + 1 hour for optional polish

---

## Questions to Consider

1. **Should we do all phases or just Phase 1?**
   - Phase 1 gives most benefit (testability)
   - Phase 2 is nice-to-have (readability)
   - Phase 3 is optional (polish)

2. **Should we add integration tests for UI?**
   - Would require Playwright or similar
   - Current unit tests may be sufficient

3. **Do we want to refactor `generate_image()` (164 lines)?**
   - Not critical but could be improved
   - Could extract loop logic to separate function

4. **Should we keep inline wrapper functions or extract all?**
   - Current plan: extract all for testability
   - Alternative: keep simple wrappers inline

---

## Recommendation

**Start with Phase 1** - it provides the most value:
- Makes code testable (inline functions → module functions)
- Extracts complex formatting logic
- Minimal risk (moving existing code)

**Then evaluate** if Phase 2 is worth it based on:
- Remaining complexity of app.py
- Future maintenance needs
- Team preferences

**Skip Phase 3** unless:
- You need comprehensive test coverage
- Planning major UI changes
- Want documentation for onboarding
