"""UI event handlers organized by feature area.

This package provides handlers for all Gradio UI events, organized into logical modules:
- generation: Image generation and plugin management
- prompt: Prompt builder and file navigation
- tokenizer: Tokenization analysis
- gallery: Gallery browser, favorites, and catalog management
- conditions: Character and facial condition generation
"""

# Re-export all handlers to maintain backward compatibility
# This allows existing imports like "from pipeworks.ui.handlers import generate_image"
# to continue working

from .conditions import (
    generate_condition_by_type,
)
from .gallery import (
    apply_gallery_filter,
    initialize_gallery_browser,
    load_gallery_folder,
    move_favorites_to_catalog,
    refresh_gallery,
    select_gallery_image,
    switch_gallery_root,
    toggle_favorite,
    toggle_metadata_format,
)
from .generation import (
    generate_image,
    get_available_models,
    set_aspect_ratio,
    switch_model_handler,
    toggle_plugin_ui,
    toggle_save_metadata_handler,
    update_plugin_config_handler,
)
from .prompt import (
    build_combined_prompt,
    get_items_in_path,
    navigate_file_selection,
)
from .tokenizer import (
    analyze_prompt,
)

__all__ = [
    # Condition handlers
    "generate_condition_by_type",
    # Generation handlers
    "generate_image",
    "get_available_models",
    "set_aspect_ratio",
    "switch_model_handler",
    "toggle_plugin_ui",
    "toggle_save_metadata_handler",
    "update_plugin_config_handler",
    # Prompt handlers
    "build_combined_prompt",
    "get_items_in_path",
    "navigate_file_selection",
    # Tokenizer handlers
    "analyze_prompt",
    # Gallery handlers
    "apply_gallery_filter",
    "initialize_gallery_browser",
    "load_gallery_folder",
    "move_favorites_to_catalog",
    "refresh_gallery",
    "select_gallery_image",
    "switch_gallery_root",
    "toggle_favorite",
    "toggle_metadata_format",
]
