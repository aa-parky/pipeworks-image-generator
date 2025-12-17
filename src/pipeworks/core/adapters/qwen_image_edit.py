"""Qwen-Image-Edit model adapter.

This module provides the adapter for the Qwen-Image-Edit model, which performs
instruction-based image editing. Unlike text-to-image models, this takes an
existing image and modifies it based on natural language instructions.

Qwen-Image-Edit Specifics
--------------------------
The Qwen-Image-Edit model is designed for:
- **Instruction-based editing**: Modify images using natural language
- **Contextual understanding**: Understands complex editing instructions
- **Preservation**: Maintains aspects of the image not mentioned in instruction
- **Multi-modal**: Combines vision and language understanding

Model Parameters
----------------
Key parameters for this model:
- **input_image**: Source image to edit (PIL Image)
- **instruction**: Natural language editing instruction
- **seed**: Random seed for reproducibility
- **num_inference_steps**: Number of denoising steps (typically 20-50)
- **guidance_scale**: Controls adherence to instruction (typically 7.5)

Usage Example
-------------
Basic image editing:

    >>> from pipeworks.core.adapters.qwen_image_edit import QwenImageEditAdapter
    >>> from pipeworks.core.config import config
    >>> from PIL import Image
    >>>
    >>> adapter = QwenImageEditAdapter(config)
    >>> base_image = Image.open("character.png")
    >>> edited = adapter.generate(
    ...     input_image=base_image,
    ...     instruction="change the character's hair color to blue",
    ...     seed=42
    ... )

With auto-save:

    >>> edited, path = adapter.generate_and_save(
    ...     input_image=base_image,
    ...     instruction="add a sword to the character's hand",
    ...     seed=42
    ... )

See Also
--------
- ModelAdapterBase: Base class for all model adapters
- ZImageTurboAdapter: Text-to-image generation adapter
- PluginBase: Plugin system documentation
"""

import logging
from datetime import datetime
from pathlib import Path

import torch
from diffusers import AutoPipelineForImage2Image
from PIL import Image

from pipeworks.core.config import PipeworksConfig
from pipeworks.core.model_adapters import ModelAdapterBase, model_registry
from pipeworks.plugins.base import PluginBase

logger = logging.getLogger(__name__)


class QwenImageEditAdapter(ModelAdapterBase):
    """Model adapter for Qwen-Image-Edit instruction-based image editing.

    This adapter wraps the Qwen-Image-Edit model pipeline, providing
    instruction-based image editing capabilities. It takes an existing image
    and modifies it based on natural language instructions.

    The adapter implements lazy loading - the model is only loaded into memory
    when generate() or generate_and_save() is first called.

    Attributes
    ----------
    name : str
        Human-readable name ("Qwen-Image-Edit")
    description : str
        Brief description of capabilities
    model_type : str
        Always "image-edit"
    config : PipeworksConfig
        Configuration object containing model and generation settings
    pipe : AutoPipelineForImage2Image | None
        HuggingFace Diffusers pipeline (None until loaded)
    plugins : list[PluginBase]
        List of active plugin instances

    Notes
    -----
    - Model loading can take 20-40 seconds depending on hardware
    - Model cache is stored in config.models_dir
    - Model size varies (check HuggingFace model card)
    - First generation after loading takes longer due to initialization
    - Unlike text-to-image models, this requires an input image

    Examples
    --------
    Basic editing:

        >>> from PIL import Image
        >>> adapter = QwenImageEditAdapter(config)
        >>> img = Image.open("base.png")
        >>> edited = adapter.generate(
        ...     input_image=img,
        ...     instruction="make the sky sunset colors",
        ...     seed=42
        ... )

    With plugins:

        >>> from pipeworks.plugins.base import plugin_registry
        >>> plugins = [plugin_registry.instantiate("Save Metadata")]
        >>> adapter = QwenImageEditAdapter(config, plugins=plugins)
        >>> edited, path = adapter.generate_and_save(
        ...     input_image=img,
        ...     instruction="add dramatic lighting",
        ...     seed=42
        ... )
    """

    name = "Qwen-Image-Edit"
    description = "Instruction-based image editing with Qwen-Image-Edit"
    model_type = "image-edit"
    version = "1.0.0"

    def __init__(
        self, config: PipeworksConfig, plugins: list[PluginBase] | None = None
    ) -> None:
        """Initialize the Qwen-Image-Edit adapter.

        Args:
            config: Configuration object containing model settings
            plugins: List of plugin instances to use
        """
        super().__init__(config, plugins)
        self.pipe: AutoPipelineForImage2Image | None = None
        self._model_loaded = False

        # Get model ID from config (should be in PIPEWORKS_QWEN_MODEL_ID env var)
        self.model_id = getattr(
            config, "qwen_model_id", "Qwen/Qwen-Image-Edit-2509"
        )
        logger.info(f"Configured Qwen-Image-Edit with model: {self.model_id}")

    def load_model(self) -> None:
        """Load the Qwen-Image-Edit model into memory.

        This method downloads the model from HuggingFace (if not cached),
        loads it into memory with the configured dtype, moves it to the
        target device, and applies any configured optimizations.

        Raises
        ------
        Exception
            If model loading fails (network issues, CUDA errors, etc.)

        Notes
        -----
        - First load downloads model files from HuggingFace
        - Subsequent loads use cache in config.models_dir
        - Model compilation (if enabled) may add time to first load
        """
        if self._model_loaded:
            logger.info("Qwen-Image-Edit model already loaded, skipping...")
            return

        logger.info(f"Loading Qwen-Image-Edit model {self.model_id}...")

        try:
            # Map dtype string to torch dtype enum
            dtype_map = {
                "bfloat16": torch.bfloat16,
                "float16": torch.float16,
                "float32": torch.float32,
            }
            torch_dtype = dtype_map[self.config.torch_dtype]

            # Load pipeline from HuggingFace Hub (or local cache)
            # Using AutoPipeline to automatically detect the correct pipeline type
            self.pipe = AutoPipelineForImage2Image.from_pretrained(
                self.model_id,
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=False,
                cache_dir=str(self.config.models_dir),
            )

            # Move model to target device
            if not self.config.enable_model_cpu_offload:
                self.pipe.to(self.config.device)
            else:
                self.pipe.enable_model_cpu_offload()
                logger.info("Enabled model CPU offloading")

            # Apply performance optimizations
            if self.config.enable_attention_slicing:
                self.pipe.enable_attention_slicing()
                logger.info("Enabled attention slicing")

            # Use alternative attention backend if configured
            if self.config.attention_backend != "default":
                # Note: Not all pipelines support all attention backends
                try:
                    if hasattr(self.pipe, "unet"):
                        self.pipe.unet.set_attention_backend(
                            self.config.attention_backend
                        )
                    elif hasattr(self.pipe, "transformer"):
                        self.pipe.transformer.set_attention_backend(
                            self.config.attention_backend
                        )
                    logger.info(
                        f"Set attention backend to: {self.config.attention_backend}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Could not set attention backend: {e}. Continuing with default."
                    )

            self._model_loaded = True
            logger.info("Qwen-Image-Edit model loaded successfully!")

        except Exception as e:
            logger.error(f"Failed to load Qwen-Image-Edit model: {e}")
            raise

    def generate(
        self,
        input_image: Image.Image,
        instruction: str,
        num_inference_steps: int | None = None,
        guidance_scale: float = 7.5,
        seed: int | None = None,
        strength: float = 0.8,
    ) -> Image.Image:
        """Edit an image based on a natural language instruction.

        Args:
            input_image: Source PIL Image to edit
            instruction: Natural language instruction for the edit
            num_inference_steps: Number of denoising steps (default 30)
            guidance_scale: How closely to follow instruction (default 7.5)
            seed: Random seed for reproducibility (None for random)
            strength: How much to transform the image (0.0-1.0, default 0.8)

        Returns
        -------
        Image.Image
            Edited PIL Image

        Raises
        ------
        Exception
            If generation fails
        ValueError
            If input_image is not provided or invalid

        Notes
        -----
        - If model is not loaded, it will be loaded automatically
        - strength controls how much the image changes (1.0 = maximum change)
        - guidance_scale controls adherence to instruction (higher = stricter)
        - Same inputs + seed = same output (reproducible)
        """
        if not self._model_loaded:
            self.load_model()

        if input_image is None:
            raise ValueError("input_image is required for image editing")

        # Use reasonable defaults for image editing
        num_inference_steps = num_inference_steps or 30

        logger.info(
            f"Editing image: steps={num_inference_steps}, "
            f"guidance={guidance_scale}, strength={strength}, seed={seed}"
        )
        logger.info(f"Instruction: {instruction}")

        # Create generator for reproducibility
        generator = None
        if seed is not None:
            generator = torch.Generator(self.config.device).manual_seed(seed)

        try:
            # Generate edited image
            # Note: The exact parameter names may vary depending on the specific
            # pipeline implementation. Adjust if needed based on Qwen's API.
            output = self.pipe(
                prompt=instruction,  # Some pipelines use 'prompt' for instruction
                image=input_image,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                strength=strength,
                generator=generator,
            )

            image = output.images[0]
            logger.info("Image edited successfully!")
            return image

        except Exception as e:
            logger.error(f"Failed to edit image: {e}")
            raise

    def generate_and_save(
        self,
        input_image: Image.Image,
        instruction: str,
        num_inference_steps: int | None = None,
        guidance_scale: float = 7.5,
        seed: int | None = None,
        strength: float = 0.8,
        output_path: Path | None = None,
    ) -> tuple[Image.Image, Path]:
        """Edit an image and save it to disk with plugin hooks.

        This method orchestrates the full editing pipeline:
        1. Call on_generate_start plugin hooks (can modify params)
        2. Edit image using potentially modified params
        3. Call on_generate_complete plugin hooks (can modify image)
        4. Determine output path (auto-generate if not provided)
        5. Call on_before_save plugin hooks (can modify image/path)
        6. Save image to disk
        7. Call on_after_save plugin hooks (e.g., metadata export)

        Args:
            input_image: Source PIL Image to edit
            instruction: Natural language instruction for the edit
            num_inference_steps: Number of denoising steps
            guidance_scale: How closely to follow instruction
            seed: Random seed for reproducibility
            strength: How much to transform the image (0.0-1.0)
            output_path: Custom output path (if None, auto-generates)

        Returns
        -------
        tuple[Image.Image, Path]
            Tuple of (edited image, save path)

        Raises
        ------
        Exception
            If editing or save fails
        """
        # Use reasonable defaults
        num_inference_steps = num_inference_steps or 30

        # Build params dict for plugins
        params = {
            "instruction": instruction,
            "prompt": instruction,  # Alias for compatibility
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "strength": strength,
            "seed": seed,
            "model_id": self.model_id,
            "model_name": self.name,
            "input_image_size": input_image.size if input_image else None,
        }

        # Plugin Hook 1: on_generate_start
        for plugin in self.plugins:
            if plugin.enabled:
                params = plugin.on_generate_start(params)

        # Generate edited image using potentially modified params
        image = self.generate(
            input_image=input_image,
            instruction=params["instruction"],
            num_inference_steps=params["num_inference_steps"],
            guidance_scale=params["guidance_scale"],
            strength=params["strength"],
            seed=params["seed"],
        )

        # Plugin Hook 2: on_generate_complete
        for plugin in self.plugins:
            if plugin.enabled:
                image = plugin.on_generate_complete(image, params)

        # Generate output filename if not provided
        # Format: pipeworks_edit_YYYYMMDD_HHMMSS_seed{seed}.png
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            seed_suffix = f"_seed{params['seed']}" if params["seed"] is not None else ""
            filename = f"pipeworks_edit_{timestamp}{seed_suffix}.png"
            output_path = self.config.outputs_dir / filename

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Plugin Hook 3: on_before_save
        for plugin in self.plugins:
            if plugin.enabled:
                image, output_path = plugin.on_before_save(image, output_path, params)

        # Save image to disk
        image.save(output_path)
        logger.info(f"Edited image saved to: {output_path}")

        # Plugin Hook 4: on_after_save
        for plugin in self.plugins:
            if plugin.enabled:
                plugin.on_after_save(image, output_path, params)

        return image, output_path

    def unload_model(self) -> None:
        """Unload the Qwen-Image-Edit model from memory.

        This method:
        1. Deletes the pipeline instance
        2. Clears CUDA cache if using GPU
        3. Resets the loaded flag
        4. Logs unload success
        """
        if self._model_loaded:
            logger.info("Unloading Qwen-Image-Edit model...")
            del self.pipe
            self.pipe = None
            self._model_loaded = False

            # Clear CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("Qwen-Image-Edit model unloaded successfully")

    @property
    def is_loaded(self) -> bool:
        """Check if the model is currently loaded.

        Returns
        -------
        bool
            True if model is loaded, False otherwise
        """
        return self._model_loaded


# Register the adapter with the global model registry
model_registry.register(QwenImageEditAdapter)
