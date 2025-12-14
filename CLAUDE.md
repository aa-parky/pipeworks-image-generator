# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pipeworks is a Python-based image generation framework designed for **programmatic control**, not visual node-based workflows. The primary goal is to create a clean Python API for image generation that can be easily integrated into game environments (e.g., MUD systems) while providing a Gradio UI for testing and experimentation.

**Key Philosophy**: The Gradio UI is a testing interface. The real value is the Python API that can be imported and used directly in other applications.

## Running the Application

```bash
# Launch Gradio UI
pipeworks
# or
python -m pipeworks.ui.app

# Access at http://0.0.0.0:7860
```

## Development Commands

```bash
# Install for development
pip install -e .
# or with dev dependencies
pip install -e ".[dev]"

# Code formatting
black src/
ruff check src/

# Type checking
mypy src/
```

## Architecture

### Core Components

**`src/pipeworks/core/pipeline.py`** - ImageGenerator class
- Wraps Z-Image-Turbo diffusers pipeline
- `generate()` returns PIL Image
- `generate_and_save()` returns tuple of (Image, Path)
- Simple interface, no complex abstractions

**`src/pipeworks/core/config.py`** - PipeworksConfig class
- Pydantic-based configuration using environment variables
- All settings prefixed with `PIPEWORKS_`
- Loaded from `.env` file (use `.env.example` as template)

**`src/pipeworks/ui/app.py`** - Gradio interface
- Single-file UI implementation
- Simple function-based metadata plugin (not class-based)
- Metadata saved to `outputs/metadata/` subfolder

**`src/pipeworks/plugins/` and `src/pipeworks/workflows/`**
- Infrastructure exists but workflows/plugins are currently implemented simply in the UI
- Future expansion planned, but keep implementations simple
- Avoid over-engineering with complex class hierarchies

### Configuration System

Configuration uses Pydantic with environment variables:
- Prefix: `PIPEWORKS_`
- Case insensitive
- Loads from `.env` file if present
- See `PipeworksConfig` in `src/pipeworks/core/config.py`

Critical settings:
- `guidance_scale` MUST be 0.0 for Z-Image-Turbo (enforced in pipeline)
- `num_inference_steps` default is 9 (optimal for Z-Image-Turbo)
- Model cache: `models/` directory (gitignored)
- Output directory: `outputs/` (gitignored)

## Z-Image-Turbo Model Constraints

The Z-Image-Turbo model has specific requirements that **must not be violated**:

1. **guidance_scale MUST be 0.0** - The pipeline enforces this with a warning
2. **num_inference_steps = 9 is optimal** - Results in 8 DiT forwards
3. **torch_dtype = bfloat16** recommended for supported GPUs
4. **16GB+ VRAM required**

These constraints are documented in the model's HuggingFace page and hardcoded into the pipeline validation.

## Programmatic Usage Pattern

The intended usage pattern for integration (e.g., into game code):

```python
from pipeworks import ImageGenerator

# Initialize once
generator = ImageGenerator()

# Generate deterministically from game state
image = generator.generate(
    prompt="rare healing potion",
    seed=hash(item_id)  # Deterministic from game ID
)
```

**Important**: Keep the API simple and importable. Avoid dependencies that would complicate integration into other Python projects.

## Plugin System (Current Implementation)

The metadata plugin is currently implemented as a **simple function** in `app.py`, not as a complex plugin class hierarchy. This was an intentional simplification from an over-engineered approach.

When enabled via UI checkbox:
- Saves `[filename].txt` with prompt
- Saves `[filename].json` with all parameters
- Files saved to configurable subfolder (default: `metadata/`)
- Optional filename prefix support

**Design Decision**: Keep plugins simple and functional. The elaborate plugin base class system exists in `src/pipeworks/plugins/base.py` but is not currently used in the UI. Future plugins should follow the simple pattern in `app.py` unless there's a clear need for the complex system.

## File Naming Convention

Generated files follow this pattern:
```
pipeworks_YYYYMMDD_HHMMSS_seed{seed}.png
```

Metadata files use the same base name:
```
metadata/pipeworks_YYYYMMDD_HHMMSS_seed{seed}.txt
metadata/pipeworks_YYYYMMDD_HHMMSS_seed{seed}.json
```

## Development History Notes

The codebase has gone through iterations. Earlier versions included:
- Complex workflow system with multiple workflow types (Character, GameAsset, CityMap)
- Elaborate plugin base classes with lifecycle hooks
- Workflow registry and plugin registry systems

These were **intentionally simplified** because they over-complicated the MVP. The infrastructure remains in the codebase for future expansion, but the current UI uses a simple, direct approach. When making changes, prefer simplicity over architectural complexity unless there's a clear use case.

## Target Deployment

Production deployment is:
- Debian Trixie server
- NVIDIA RTX 5090 (24GB VRAM)
- Local network only (Tailscale for security)
- No external/cloud dependencies

The application should remain local-first and not require internet connectivity after initial model download.
