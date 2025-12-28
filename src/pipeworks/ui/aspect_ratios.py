"""Aspect ratio presets, validation, and utilities for image generation.

This module provides:
- AspectRatioPreset dataclass with rich metadata
- Validation functions for dimensions and preset names
- Utility functions for preset management and lookups
- Backward-compatible ASPECT_RATIOS dict

The aspect ratio system validates dimensions against Z-Image-Turbo constraints:
- Dimensions must be positive integers
- Range: 64-2048 pixels
- Must be multiples of 64 (diffusion model requirement)
"""

from dataclasses import dataclass
from math import gcd

from pipeworks.core.config import PipeworksConfig


class PresetCategory:
    """Preset categories for organization and filtering."""

    STANDARD = "standard"
    SOCIAL_MEDIA = "social_media"
    PHOTOGRAPHY = "photography"
    PRINT = "print"
    CUSTOM = "custom"


@dataclass(frozen=True)
class AspectRatioPreset:
    """Immutable aspect ratio preset with rich metadata.

    Attributes:
        name: Display name (e.g., "Square 1:1 (1024x1024)")
        width: Width in pixels (None for custom)
        height: Height in pixels (None for custom)
        ratio_string: Aspect ratio as string (e.g., "1:1", "16:9")
        category: Preset category (from PresetCategory)
        description: Human-readable description
    """

    name: str
    width: int | None
    height: int | None
    ratio_string: str
    category: str
    description: str = ""

    @property
    def is_landscape(self) -> bool:
        """Check if preset is landscape orientation."""
        if self.width is None or self.height is None:
            return False
        return self.width > self.height

    @property
    def is_portrait(self) -> bool:
        """Check if preset is portrait orientation."""
        if self.width is None or self.height is None:
            return False
        return self.height > self.width

    @property
    def is_square(self) -> bool:
        """Check if preset is square."""
        if self.width is None or self.height is None:
            return False
        return self.width == self.height

    @property
    def is_custom(self) -> bool:
        """Check if this is the custom preset."""
        return self.width is None and self.height is None

    @property
    def dimensions_tuple(self) -> tuple[int, int] | None:
        """Get (width, height) tuple for backward compatibility."""
        if self.width is None or self.height is None:
            return None
        return (self.width, self.height)


# Preset definitions (internal)
_PRESET_LIST: list[AspectRatioPreset] = [
    AspectRatioPreset(
        name="Square 1:1 (1024x1024)",
        width=1024,
        height=1024,
        ratio_string="1:1",
        category=PresetCategory.STANDARD,
        description="Perfect square for Instagram posts and profile pictures",
    ),
    AspectRatioPreset(
        name="Widescreen 16:9 (1280x720)",
        width=1280,
        height=720,
        ratio_string="16:9",
        category=PresetCategory.SOCIAL_MEDIA,
        description="Standard HD video and YouTube thumbnails",
    ),
    AspectRatioPreset(
        name="Widescreen 16:9 (1600x896)",
        width=1600,
        height=896,
        ratio_string="16:9",
        category=PresetCategory.SOCIAL_MEDIA,
        description="High resolution widescreen for video content",
    ),
    AspectRatioPreset(
        name="Portrait 9:16 (720x1280)",
        width=720,
        height=1280,
        ratio_string="9:16",
        category=PresetCategory.SOCIAL_MEDIA,
        description="Vertical format for Instagram Stories and TikTok",
    ),
    AspectRatioPreset(
        name="Portrait 9:16 (896x1600)",
        width=896,
        height=1600,
        ratio_string="9:16",
        category=PresetCategory.SOCIAL_MEDIA,
        description="High resolution vertical format for mobile content",
    ),
    AspectRatioPreset(
        name="Standard 3:2 (1280x832)",
        width=1280,
        height=832,
        ratio_string="3:2",
        category=PresetCategory.PHOTOGRAPHY,
        description="Classic photography aspect ratio, DSLR standard",
    ),
    AspectRatioPreset(
        name="Standard 2:3 (832x1280)",
        width=832,
        height=1280,
        ratio_string="2:3",
        category=PresetCategory.PHOTOGRAPHY,
        description="Portrait orientation photography standard",
    ),
    AspectRatioPreset(
        name="Standard 3:2 (1536x1024)",
        width=1536,
        height=1024,
        ratio_string="3:2",
        category=PresetCategory.PHOTOGRAPHY,
        description="High resolution photography standard",
    ),
    AspectRatioPreset(
        name="Custom",
        width=None,
        height=None,
        ratio_string="custom",
        category=PresetCategory.CUSTOM,
        description="Use custom dimensions from config defaults",
    ),
]

# Backward compatibility: maintain the same dict structure
ASPECT_RATIOS: dict[str, tuple[int, int] | None] = {
    preset.name: preset.dimensions_tuple for preset in _PRESET_LIST
}


class AspectRatioValidationError(Exception):
    """Raised when aspect ratio validation fails."""

    pass


def validate_dimensions(width: int, height: int) -> None:
    """Validate aspect ratio dimensions.

    Args:
        width: Image width in pixels
        height: Image height in pixels

    Raises:
        AspectRatioValidationError: If dimensions are invalid
    """
    # Check positive integers
    if width <= 0 or height <= 0:
        raise AspectRatioValidationError(
            f"Dimensions must be positive integers. Got: {width}x{height}"
        )

    # Check reasonable bounds (match Z-Image-Turbo constraints)
    min_dimension = 64
    max_dimension = 2048

    if width < min_dimension or height < min_dimension:
        raise AspectRatioValidationError(
            f"Dimensions must be at least {min_dimension}px. Got: {width}x{height}"
        )

    if width > max_dimension or height > max_dimension:
        raise AspectRatioValidationError(
            f"Dimensions must not exceed {max_dimension}px. Got: {width}x{height}"
        )

    # Check alignment (must be multiple of 64 for diffusion models)
    if width % 64 != 0 or height % 64 != 0:
        nearest_width = round(width / 64) * 64
        nearest_height = round(height / 64) * 64
        raise AspectRatioValidationError(
            f"Dimensions must be multiples of 64. "
            f"Got: {width}x{height}. "
            f"Nearest valid: {nearest_width}x{nearest_height}"
        )


def validate_preset_name(name: str) -> None:
    """Validate that a preset name exists.

    Args:
        name: Preset name to validate

    Raises:
        AspectRatioValidationError: If preset doesn't exist
    """
    if name not in ASPECT_RATIOS:
        raise AspectRatioValidationError(
            f"Unknown preset: '{name}'. Available: {list(ASPECT_RATIOS.keys())}"
        )


def calculate_aspect_ratio(width: int, height: int) -> str:
    """Calculate aspect ratio string from dimensions.

    Uses GCD to find simplest ratio representation.

    Args:
        width: Image width
        height: Image height

    Returns:
        Aspect ratio as string (e.g., "16:9", "3:2")

    Example:
        >>> calculate_aspect_ratio(1920, 1080)
        '16:9'
        >>> calculate_aspect_ratio(1024, 1024)
        '1:1'
    """
    divisor = gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def get_preset_by_name(name: str) -> AspectRatioPreset:
    """Get preset by name.

    Args:
        name: Preset name

    Returns:
        AspectRatioPreset instance

    Raises:
        AspectRatioValidationError: If preset not found

    Example:
        >>> preset = get_preset_by_name("Square 1:1 (1024x1024)")
        >>> preset.is_square
        True
    """
    validate_preset_name(name)
    for preset in _PRESET_LIST:
        if preset.name == name:
            return preset
    # Should never reach here if validation passed
    raise AspectRatioValidationError(f"Preset '{name}' not found")


def list_preset_names() -> list[str]:
    """Get list of all preset names.

    Returns:
        List of preset names in definition order

    Example:
        >>> names = list_preset_names()
        >>> "Square 1:1 (1024x1024)" in names
        True
    """
    return [preset.name for preset in _PRESET_LIST]


def get_presets_by_category(category: str) -> list[AspectRatioPreset]:
    """Get all presets in a category.

    Args:
        category: Category name (from PresetCategory)

    Returns:
        List of presets in the category

    Example:
        >>> social = get_presets_by_category(PresetCategory.SOCIAL_MEDIA)
        >>> len(social) > 0
        True
    """
    return [preset for preset in _PRESET_LIST if preset.category == category]


def get_dimensions(preset_name: str, config: PipeworksConfig) -> tuple[int, int]:
    """Get dimensions for a preset, using config defaults for Custom.

    This is the main function for UI handlers to use.

    Args:
        preset_name: Name of the preset
        config: Config instance for default dimensions

    Returns:
        (width, height) tuple

    Raises:
        AspectRatioValidationError: If preset doesn't exist

    Example:
        >>> from pipeworks.core.config import config
        >>> width, height = get_dimensions("Square 1:1 (1024x1024)", config)
        >>> width, height
        (1024, 1024)
    """
    preset = get_preset_by_name(preset_name)

    if preset.is_custom:
        return (config.default_width, config.default_height)

    # At this point, width and height are guaranteed to be int (not None)
    assert preset.width is not None and preset.height is not None
    return (preset.width, preset.height)


def find_preset_for_dimensions(width: int, height: int) -> AspectRatioPreset | None:
    """Find preset that matches given dimensions.

    Args:
        width: Image width
        height: Image height

    Returns:
        Matching preset or None if no match

    Example:
        >>> preset = find_preset_for_dimensions(1024, 1024)
        >>> preset.name if preset else None
        'Square 1:1 (1024x1024)'
    """
    for preset in _PRESET_LIST:
        if not preset.is_custom and preset.width == width and preset.height == height:
            return preset
    return None
