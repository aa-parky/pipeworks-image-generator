"""Model adapters for Pipeworks.

This package contains model-specific adapters that implement the ModelAdapterBase
interface. Each adapter handles the specifics of a particular AI model while
providing a consistent API.

Available Adapters
------------------
- ZImageTurboAdapter: Fast text-to-image generation with Z-Image-Turbo
- QwenImageEditAdapter: Image editing with instruction-based modifications

Usage
-----
Adapters are typically instantiated through the model registry:

    >>> from pipeworks.core.model_adapters import model_registry
    >>> from pipeworks.core.config import config
    >>>
    >>> adapter = model_registry.instantiate("Z-Image-Turbo", config)
    >>> image = adapter.generate(prompt="test", seed=42)

Direct import is also possible:

    >>> from pipeworks.core.adapters.zimage_turbo import ZImageTurboAdapter
    >>> adapter = ZImageTurboAdapter(config)
"""

from .qwen_image_edit import QwenImageEditAdapter
from .zimage_turbo import ZImageTurboAdapter

__all__ = ["ZImageTurboAdapter", "QwenImageEditAdapter"]
