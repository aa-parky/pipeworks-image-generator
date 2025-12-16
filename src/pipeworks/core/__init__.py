"""Core functionality for image generation.

This module provides the core components for the Pipeworks Image Generator:

- **ImageGenerator**: Main pipeline wrapper for Z-Image-Turbo model inference
- **PipeworksConfig**: Configuration management using Pydantic Settings
- **config**: Global configuration instance (loads from environment variables)

The core module is designed to be the primary interface for image generation,
abstracting the complexity of the Z-Image-Turbo model and providing a clean,
plugin-extensible API.

Architecture Overview
---------------------
The core module follows a layered architecture:

1. **Configuration Layer** (config.py):
   - Environment-based configuration using Pydantic Settings
   - All settings prefixed with PIPEWORKS_ in .env files
   - Automatic directory creation and path resolution

2. **Pipeline Layer** (pipeline.py):
   - Wraps HuggingFace Diffusers ZImagePipeline
   - Manages model loading, optimization, and lifecycle
   - Implements plugin hooks for extensibility

3. **Support Utilities**:
   - prompt_builder.py: File-based prompt construction
   - tokenizer.py: Token analysis for prompts
   - gallery_browser.py: Image browsing and metadata display
   - favorites_db.py: SQLite-based favorites tracking
   - catalog_manager.py: Archive management for favorited images

Usage Example
-------------
    from pipeworks.core import ImageGenerator, config

    # Initialize generator with global config
    generator = ImageGenerator()

    # Generate and save an image
    image, path = generator.generate_and_save(
        prompt="a beautiful landscape",
        seed=42
    )

    print(f"Image saved to: {path}")

See Also
--------
- ImageGenerator: Full API documentation for generation pipeline
- PipeworksConfig: Configuration options and environment variables
"""

from pipeworks.core.config import PipeworksConfig, config
from pipeworks.core.pipeline import ImageGenerator

__all__ = [
    "ImageGenerator",
    "PipeworksConfig",
    "config",
]
