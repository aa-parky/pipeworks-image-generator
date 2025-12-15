"""Formatting utilities for UI output messages."""

from .models import GenerationParams
from .validation import ValidationError


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
        paths_display = f"{len(generated_paths)} images saved to output folder"

    # Build dynamic prompt info
    dynamic_info = ""
    if has_dynamic:
        dynamic_info = "\n**Dynamic Prompts:** Enabled (prompts rebuilt for each image)"
        if prompts_used:
            if len(prompts_used) <= 3:
                # Show all prompts if 3 or fewer
                dynamic_info += f"\n**Sample Prompts:** {', '.join(prompts_used[:3])}"
            else:
                # Show first 2 prompts as samples
                dynamic_info += f"\n**Sample Prompts:** {prompts_used[0]}, {prompts_used[1]}, ..."

    # Build plugins info
    plugins_info = f"\n**Active Plugins:** {', '.join(active_plugins)}" if active_plugins else ""

    # Format final message
    total_info = f"**Total:** {params.total_images} images"
    batch_info = f"**Batch Size:** {params.batch_size} × **Runs:** {params.runs} = {total_info}"
    return f"""
✅ **Generation Complete!**

**Prompt:** {params.prompt if not has_dynamic else "(Dynamic)"}
**Dimensions:** {params.width}x{params.height}
**Steps:** {params.num_steps}
{batch_info}
**Seeds:** {seeds_display}
**Saved to:** {paths_display}{dynamic_info}{plugins_info}
    """.strip()


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
        f"❌ **Error**\n\nAn unexpected error occurred. "
        f"Check logs for details.\n\n`{str(error)}`"
    )
