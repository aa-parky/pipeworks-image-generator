"""Pipeline wrapper for Z-Image-Turbo model.

This module provides the ImageGenerator class, which wraps HuggingFace's
ZImagePipeline for the Z-Image-Turbo model. It handles model loading,
optimization, generation, and plugin lifecycle management.

Key Features
------------
- **Lazy Loading**: Model is only loaded when first needed
- **Plugin System**: Extensible hooks for custom behavior
- **Automatic Optimization**: Applies configured performance optimizations
- **Z-Image-Turbo Constraints**: Enforces required settings (guidance_scale=0.0)
- **Reproducibility**: Seed-based generation for consistent results
- **Resource Management**: Proper model unloading and CUDA cache clearing

Plugin Lifecycle Hooks
----------------------
The ImageGenerator supports four plugin hooks during generation:

1. **on_generate_start(params)**: Called before generation
   - Can modify generation parameters
   - Useful for parameter validation or preprocessing

2. **on_generate_complete(image, params)**: Called after generation
   - Can modify the generated image
   - Useful for post-processing or filtering

3. **on_before_save(image, path, params)**: Called before saving
   - Can modify image or save path
   - Useful for custom naming or format conversion

4. **on_after_save(image, path, params)**: Called after saving
   - Cannot modify image or path
   - Useful for metadata export or notifications

Z-Image-Turbo Specifics
------------------------
The Z-Image-Turbo model has specific requirements:
- **guidance_scale**: Must be 0.0 (automatically enforced)
- **Optimal steps**: 9 inference steps (results in 8 DiT forwards)
- **Recommended dtype**: bfloat16 for best quality/performance
- **Device**: CUDA preferred, falls back to CPU

Model Optimization Options
---------------------------
The pipeline supports several optimizations (configured via PipeworksConfig):
- **Attention Slicing**: Reduces VRAM usage at slight speed cost
- **CPU Offloading**: Moves model layers to CPU when not in use
- **Model Compilation**: Uses torch.compile for faster inference
- **Flash Attention**: Can use Flash-Attention-2 backend for speedup

Usage Example
-------------
Basic generation:

    >>> from pipeworks.core import ImageGenerator
    >>> generator = ImageGenerator()
    >>> image = generator.generate(
    ...     prompt="a beautiful landscape",
    ...     seed=42
    ... )

With plugins:

    >>> from pipeworks.plugins.base import plugin_registry
    >>> metadata_plugin = plugin_registry.instantiate("Save Metadata")
    >>> generator = ImageGenerator(plugins=[metadata_plugin])
    >>> image, path = generator.generate_and_save(
    ...     prompt="a beautiful landscape",
    ...     seed=42
    ... )

See Also
--------
- ZImagePipeline: HuggingFace Diffusers pipeline documentation
- PluginBase: Plugin system documentation
- PipeworksConfig: Configuration options
"""

import logging
from datetime import datetime
from pathlib import Path

import torch
from diffusers import ZImagePipeline
from PIL import Image

from pipeworks.plugins.base import PluginBase

from .config import PipeworksConfig
from .config import config as default_config

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Main image generation pipeline wrapper for Z-Image-Turbo.

    This class wraps the HuggingFace Diffusers ZImagePipeline, providing a
    simplified interface for image generation with Z-Image-Turbo. It handles
    model lifecycle, optimization, and plugin integration.

    The generator implements lazy loading - the model is only loaded into memory
    when generate() or generate_and_save() is first called. This reduces startup
    time and memory usage when the generator is initialized but not immediately used.

    Attributes
    ----------
    config : PipeworksConfig
        Configuration object containing model and generation settings
    pipe : ZImagePipeline | None
        HuggingFace Diffusers pipeline (None until loaded)
    plugins : list[PluginBase]
        List of active plugin instances

    Notes
    -----
    - Model loading can take 10-30 seconds depending on hardware and network
    - The model cache is stored in config.models_dir (typically ./models/)
    - Model size is approximately 12GB for Z-Image-Turbo
    - First generation after loading takes longer due to CUDA initialization

    Examples
    --------
    Basic usage:

        >>> generator = ImageGenerator()
        >>> image = generator.generate(
        ...     prompt="a serene mountain landscape",
        ...     width=1024,
        ...     height=1024,
        ...     num_inference_steps=9,
        ...     seed=42
        ... )
        >>> image.save("output.png")

    With plugins and auto-save:

        >>> from pipeworks.plugins.base import plugin_registry
        >>> plugins = [
        ...     plugin_registry.instantiate("Save Metadata"),
        ... ]
        >>> generator = ImageGenerator(plugins=plugins)
        >>> image, path = generator.generate_and_save(
        ...     prompt="a serene mountain landscape",
        ...     seed=42
        ... )
        >>> print(f"Saved to: {path}")

    Resource cleanup:

        >>> generator.unload_model()  # Free VRAM/RAM
    """

    def __init__(
        self, config: PipeworksConfig | None = None, plugins: list[PluginBase] | None = None
    ):
        """
        Initialize the image generator.

        Args:
            config: Configuration object. If None, uses global default config.
            plugins: List of plugin instances to use
        """
        self.config = config or default_config
        self.pipe: ZImagePipeline | None = None
        self._model_loaded = False
        self.plugins: list[PluginBase] = plugins or []

        logger.info(f"Initialized ImageGenerator with model: {self.config.model_id}")
        if self.plugins:
            logger.info(f"Loaded {len(self.plugins)} plugins: {[p.name for p in self.plugins]}")

    def load_model(self) -> None:
        """Load the Z-Image-Turbo model into memory.

        This method downloads the model from HuggingFace (if not cached),
        loads it into memory with the configured dtype, moves it to the
        target device, and applies any configured optimizations.

        The loading process follows these steps:
        1. Check if model is already loaded (skip if so)
        2. Map dtype string to torch dtype enum
        3. Load pipeline from HuggingFace (or local cache)
        4. Move model to target device (CUDA/CPU)
        5. Apply performance optimizations (attention slicing, compilation, etc.)
        6. Mark model as loaded

        Raises
        ------
        Exception
            If model loading fails (network issues, CUDA errors, etc.)

        Notes
        -----
        - First load downloads ~12GB model files from HuggingFace
        - Subsequent loads use cache in config.models_dir
        - Model compilation (if enabled) adds 1-2 minutes to first load
        - CUDA initialization happens on first generation, not during load
        """
        if self._model_loaded:
            logger.info("Model already loaded, skipping...")
            return

        logger.info(f"Loading model {self.config.model_id}...")

        try:
            # Map dtype string to torch dtype enum
            # bfloat16 is recommended for best quality/performance balance
            dtype_map = {
                "bfloat16": torch.bfloat16,
                "float16": torch.float16,
                "float32": torch.float32,
            }
            torch_dtype = dtype_map[self.config.torch_dtype]

            # Load pipeline from HuggingFace Hub (or local cache)
            # low_cpu_mem_usage=False ensures faster loading at cost of higher peak RAM
            self.pipe = ZImagePipeline.from_pretrained(
                self.config.model_id,
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=False,
                cache_dir=str(self.config.models_dir),
            )

            # Move model to target device (CUDA preferred for speed)
            # If CPU offloading is enabled, model components are moved dynamically
            if not self.config.enable_model_cpu_offload:
                # Standard approach: keep entire model on device
                self.pipe.to(self.config.device)
            else:
                # Memory-efficient approach: move layers to CPU when not in use
                self.pipe.enable_model_cpu_offload()
                logger.info("Enabled model CPU offloading")

            # Apply performance optimizations
            # Attention slicing reduces VRAM usage at slight speed cost
            if self.config.enable_attention_slicing:
                self.pipe.enable_attention_slicing()
                logger.info("Enabled attention slicing")

            # Use alternative attention backend (e.g., Flash-Attention-2)
            if self.config.attention_backend != "default":
                self.pipe.transformer.set_attention_backend(self.config.attention_backend)
                logger.info(f"Set attention backend to: {self.config.attention_backend}")

            # Compile model with torch.compile for faster inference
            # First run is slower, subsequent runs are faster
            if self.config.compile_model:
                logger.info("Compiling model (this may take a while on first run)...")
                self.pipe.transformer.compile()
                logger.info("Model compiled successfully")

            self._model_loaded = True
            logger.info("Model loaded successfully!")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def generate(
        self,
        prompt: str,
        width: int | None = None,
        height: int | None = None,
        num_inference_steps: int | None = None,
        seed: int | None = None,
        guidance_scale: float | None = None,
    ) -> Image.Image:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the image to generate
            width: Image width (default from config)
            height: Image height (default from config)
            num_inference_steps: Number of denoising steps (default from config)
            seed: Random seed for reproducibility (None for random)
            guidance_scale: Guidance scale (should be 0.0 for Turbo)

        Returns:
            Generated PIL Image
        """
        if not self._model_loaded:
            self.load_model()

        # Use config defaults if not specified
        width = width or self.config.default_width
        height = height or self.config.default_height
        num_inference_steps = num_inference_steps or self.config.num_inference_steps
        guidance_scale = (
            guidance_scale if guidance_scale is not None else self.config.guidance_scale
        )

        # Validate guidance_scale for Turbo models
        # Z-Image-Turbo REQUIRES guidance_scale=0.0 for proper operation
        # This is a hard constraint of the Turbo architecture
        if guidance_scale != 0.0:
            logger.warning(
                f"guidance_scale is {guidance_scale} but should be 0.0 for Turbo models. "
                "Setting to 0.0."
            )
            guidance_scale = 0.0

        logger.info(f"Generating image: {width}x{height}, steps={num_inference_steps}, seed={seed}")
        logger.info(f"Prompt: {prompt}")

        # Create generator for reproducibility
        # When seed is provided, torch.Generator ensures deterministic results
        # Same seed + prompt + params = same image
        generator = None
        if seed is not None:
            generator = torch.Generator(self.config.device).manual_seed(seed)

        try:
            # Generate image
            output = self.pipe(
                prompt=prompt,
                height=height,
                width=width,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
            )

            image = output.images[0]
            logger.info("Image generated successfully!")
            return image

        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            raise

    def generate_and_save(
        self,
        prompt: str,
        width: int | None = None,
        height: int | None = None,
        num_inference_steps: int | None = None,
        seed: int | None = None,
        guidance_scale: float | None = None,
        output_path: Path | None = None,
    ) -> tuple[Image.Image, Path]:
        """
        Generate an image and save it to disk.

        Args:
            prompt: Text description of the image to generate
            width: Image width
            height: Image height
            num_inference_steps: Number of denoising steps
            seed: Random seed for reproducibility
            guidance_scale: Guidance scale
            output_path: Custom output path (if None, auto-generates in outputs_dir)

        Returns:
            Tuple of (generated image, save path)
        """
        # Use config defaults if not specified
        width = width or self.config.default_width
        height = height or self.config.default_height
        num_inference_steps = num_inference_steps or self.config.num_inference_steps
        guidance_scale = (
            guidance_scale if guidance_scale is not None else self.config.guidance_scale
        )

        # Build params dict for plugins
        params = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_inference_steps": num_inference_steps,
            "seed": seed,
            "guidance_scale": guidance_scale,
            "model_id": self.config.model_id,
        }

        # Plugin Hook 1: on_generate_start
        # Allows plugins to modify generation parameters before generation
        # Example use: parameter validation, prompt preprocessing, etc.
        for plugin in self.plugins:
            if plugin.enabled:
                params = plugin.on_generate_start(params)

        # Generate image using potentially modified params from plugins
        image = self.generate(
            prompt=params["prompt"],
            width=params["width"],
            height=params["height"],
            num_inference_steps=params["num_inference_steps"],
            seed=params["seed"],
            guidance_scale=params["guidance_scale"],
        )

        # Plugin Hook 2: on_generate_complete
        # Allows plugins to modify the generated image after generation
        # Example use: post-processing, filtering, watermarking, etc.
        for plugin in self.plugins:
            if plugin.enabled:
                image = plugin.on_generate_complete(image, params)

        # Generate output filename if not provided by caller
        # Format: pipeworks_YYYYMMDD_HHMMSS_seed{seed}.png
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            seed_suffix = f"_seed{params['seed']}" if params["seed"] is not None else ""
            filename = f"pipeworks_{timestamp}{seed_suffix}.png"
            output_path = self.config.outputs_dir / filename

        # Ensure parent directory exists (handles nested paths)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Plugin Hook 3: on_before_save
        # Allows plugins to modify image or path before saving
        # Example use: custom naming, format conversion, path organization
        for plugin in self.plugins:
            if plugin.enabled:
                image, output_path = plugin.on_before_save(image, output_path, params)

        # Save image to disk
        image.save(output_path)
        logger.info(f"Image saved to: {output_path}")

        # Plugin Hook 4: on_after_save
        # Allows plugins to perform actions after saving (cannot modify image/path)
        # Example use: metadata export, notifications, database updates
        for plugin in self.plugins:
            if plugin.enabled:
                plugin.on_after_save(image, output_path, params)

        return image, output_path

    def unload_model(self) -> None:
        """Unload the model from memory."""
        if self._model_loaded:
            logger.info("Unloading model...")
            del self.pipe
            self.pipe = None
            self._model_loaded = False

            # Clear CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("Model unloaded successfully")
