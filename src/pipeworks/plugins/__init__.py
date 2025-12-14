"""Plugin system for extending Pipeworks functionality.

Plugins provide modular capabilities that can be attached to any workflow:
- SaveMetadataPlugin: Save prompts and parameters to .txt and .json files
- Future: UpscalePlugin, StyleTransferPlugin, BatchProcessPlugin, etc.

Plugins hook into the generation lifecycle:
- on_generate_start: Before generation begins
- on_generate_complete: After image is generated
- on_before_save: Before image is saved
- on_after_save: After image is saved
"""

from pipeworks.plugins.base import PluginBase, PluginRegistry, plugin_registry
from pipeworks.plugins.save_metadata import SaveMetadataPlugin

__all__ = [
    "PluginBase",
    "PluginRegistry",
    "plugin_registry",
    "SaveMetadataPlugin",
]
