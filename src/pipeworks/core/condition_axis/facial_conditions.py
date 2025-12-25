"""Facial condition generation system for character rendering.

This module implements a structured system for generating facial signal descriptors
that modulate how a character's face is perceived by the renderer. Unlike anatomical
specifications, these signals bias interpretation rather than define explicit features.

IMPORTANT: This module is designed as a standalone experiment to test how facial
signals interact with character conditions (from character_conditions.py). It is
LIKELY TO BE MERGED into character_conditions.py once the interaction patterns are
validated and appropriate cross-system exclusion rules are identified.

Design Philosophy:
    Facial signals are perceptual modifiers, not anatomical specifications:
    - "sharp-featured" → biases toward angular interpretation
    - "soft-featured" → biases toward rounded interpretation
    - "weathered" → applies wear/age texture signal
    - "understated" → reduces feature prominence
    - "pronounced" → increases feature prominence
    - "exaggerated" → pushes features toward extremes
    - "asymmetrical" → introduces irregularity signal

Example usage:
    >>> from pipeworks.core.condition_axis import generate_facial_condition
    >>> facial = generate_facial_condition(seed=42)
    >>> print(facial)
    {'facial_signal': 'weathered'}

    >>> from pipeworks.core.condition_axis import facial_condition_to_prompt
    >>> prompt_fragment = facial_condition_to_prompt(facial)
    >>> print(prompt_fragment)
    'weathered'

Architecture:
    1. FACIAL_AXES: Define all possible facial signal values
    2. FACIAL_POLICY: Rules for axis selection (facial_signal is mandatory)
    3. FACIAL_WEIGHTS: Statistical distribution for realistic variety
    4. FACIAL_EXCLUSIONS: Semantic constraints within facial system
    5. Generator: Produces constrained random combinations
    6. Converter: Transforms structured data into prompt text

Future Integration:
    When merged into character_conditions.py, cross-system exclusions will be needed:
    - age="young" + facial_signal="weathered" (likely conflict)
    - health="sickly" + facial_signal="soft-featured" (possible redundancy)
    - age="ancient" + facial_signal="understated" (may be incoherent)

    The separate module allows empirical testing of these interactions before
    encoding them into the combined exclusion rules.
"""

import logging
import random
from typing import Any

from ._base import apply_exclusion_rules, values_to_prompt, weighted_choice

logger = logging.getLogger(__name__)

# ============================================================================
# AXIS DEFINITIONS - Single Source of Truth for Facial Signals
# ============================================================================

FACIAL_AXES: dict[str, list[str]] = {
    # Facial feature perception modifiers
    # NOTE: These are mutually exclusive signals - a face is generally either
    # "sharp-featured" OR "soft-featured", not both. The max_optional=1 policy
    # enforces this at the generation level.
    "facial_signal": [
        "understated",  # Reduces feature prominence
        "pronounced",  # Increases feature prominence
        "exaggerated",  # Pushes features toward extremes
        "asymmetrical",  # Introduces irregularity
        "weathered",  # Applies wear/age texture
        "soft-featured",  # Biases toward rounded interpretation
        "sharp-featured",  # Biases toward angular interpretation
    ],
}

# ============================================================================
# AXIS POLICY - Controls Facial Signal Selection
# ============================================================================

FACIAL_POLICY: dict[str, Any] = {
    # Facial signal is mandatory - when this module is called, always generate a signal
    # This ensures consistent behavior: if user explicitly requests facial conditions,
    # they always get one (not a 50% chance of empty result)
    "mandatory": ["facial_signal"],
    # No optional axes - we always generate exactly one facial signal
    "optional": [],
    # max_optional not used since optional list is empty
    "max_optional": 0,
}

# ============================================================================
# WEIGHTS - Statistical Distribution for Facial Signals
# ============================================================================

FACIAL_WEIGHTS: dict[str, dict[str, float]] = {
    # Facial signal distribution: skewed toward subtle/neutral signals
    "facial_signal": {
        "understated": 3.0,  # Common - most faces aren't remarkable
        "soft-featured": 2.5,  # Fairly common
        "pronounced": 2.0,  # Moderate
        "sharp-featured": 2.0,  # Moderate
        "weathered": 1.5,  # Less common (requires age/experience)
        "asymmetrical": 1.0,  # Uncommon
        "exaggerated": 0.5,  # Rare - extreme features
    },
}

# ============================================================================
# EXCLUSIONS - Semantic Coherence Rules (Within Facial System)
# ============================================================================

# NOTE: Most exclusions will be cross-system (facial + character conditions)
# and will be implemented when this module is merged into character_conditions.py.
# For now, we define only the most obvious internal conflicts.

FACIAL_EXCLUSIONS: dict[tuple[str, str], dict[str, list[str]]] = {
    # Internal facial system exclusions (conceptual opposites)
    # These are technically prevented by max_optional=1, but explicitly
    # documented here for clarity and future-proofing.
    # Note: With max_optional=1, these exclusions are redundant but serve as
    # documentation of the design intent. If max_optional is increased in the
    # future, these rules become critical.
}

# ============================================================================
# GENERATOR FUNCTIONS
# ============================================================================


def generate_facial_condition(seed: int | None = None) -> dict[str, str]:
    """Generate a facial signal condition using weighted random selection.

    This function applies the facial signal rule system:
    1. Select mandatory facial_signal axis (always included)
    2. Apply weighted probability distributions
    3. Apply semantic exclusion rules (currently minimal)
    4. Return structured condition data

    NOTE: Always returns a facial signal. This ensures consistent behavior when
    users explicitly request facial conditions - they always get one.

    Args:
        seed: Optional random seed for reproducible generation.
             If None, uses system entropy (non-reproducible).

    Returns:
        Dictionary mapping axis names to selected values.
        Always contains exactly one key: "facial_signal"
        Example: {"facial_signal": "weathered"}

    Examples:
        >>> # Reproducible generation
        >>> cond1 = generate_facial_condition(seed=42)
        >>> cond2 = generate_facial_condition(seed=42)
        >>> cond1 == cond2
        True

        >>> # Non-reproducible (different each call)
        >>> generate_facial_condition()
        {'facial_signal': 'soft-featured'}

        >>> # Always returns a facial signal
        >>> generate_facial_condition(seed=123)
        {'facial_signal': 'sharp-featured'}
    """
    # Set random seed for reproducibility if provided
    if seed is not None:
        random.seed(seed)

    chosen: dict[str, str] = {}

    # ========================================================================
    # PHASE 1: Select mandatory axes
    # Currently empty for facial signals (all are optional)
    # ========================================================================
    for axis in FACIAL_POLICY["mandatory"]:
        if axis not in FACIAL_AXES:
            logger.warning(f"Mandatory axis '{axis}' not defined in FACIAL_AXES")
            continue

        chosen[axis] = weighted_choice(FACIAL_AXES[axis], FACIAL_WEIGHTS.get(axis))
        logger.debug(f"Mandatory axis selected: {axis} = {chosen[axis]}")

    # ========================================================================
    # PHASE 2: Select optional axes
    # Randomly pick 0 to max_optional axes (currently 0 or 1)
    # ========================================================================
    max_optional = FACIAL_POLICY.get("max_optional", 1)
    num_optional = random.randint(0, min(max_optional, len(FACIAL_POLICY["optional"])))

    # Randomly sample without replacement
    optional_axes = random.sample(FACIAL_POLICY["optional"], num_optional)
    logger.debug(f"Selected {num_optional} optional axes: {optional_axes}")

    for axis in optional_axes:
        if axis not in FACIAL_AXES:
            logger.warning(f"Optional axis '{axis}' not defined in FACIAL_AXES")
            continue

        chosen[axis] = weighted_choice(FACIAL_AXES[axis], FACIAL_WEIGHTS.get(axis))
        logger.debug(f"Optional axis selected: {axis} = {chosen[axis]}")

    # ========================================================================
    # PHASE 3: Apply semantic exclusion rules
    # Currently minimal - most exclusions will be cross-system
    # ========================================================================
    apply_exclusion_rules(chosen, FACIAL_EXCLUSIONS)

    return chosen


def facial_condition_to_prompt(condition_dict: dict[str, str]) -> str:
    """Convert structured facial condition data to a prompt fragment.

    This is the only place structured data becomes prose text.
    The output is designed to be clean and diffusion-friendly.

    NOTE: When merged into character_conditions.py, this function will be
    replaced by the existing condition_to_prompt() function.

    Args:
        condition_dict: Dictionary mapping axis names to values
                       (output from generate_facial_condition)

    Returns:
        Comma-separated string of condition values.
        Since facial_signal is mandatory, always returns a single word
        (e.g., "weathered", "sharp-featured")

    Examples:
        >>> facial_condition_to_prompt({"facial_signal": "weathered"})
        'weathered'

        >>> facial_condition_to_prompt({"facial_signal": "sharp-featured"})
        'sharp-featured'

    Notes:
        - Order is determined by dict iteration (Python 3.7+ preserves insertion order)
        - Since facial_signal is mandatory, output is always a single word
        - Empty dict returns empty string (for backward compatibility only)
    """
    return values_to_prompt(condition_dict)


def get_available_facial_axes() -> list[str]:
    """Get list of all defined facial condition axes.

    Returns:
        List of axis names (currently just ['facial_signal'])

    Example:
        >>> get_available_facial_axes()
        ['facial_signal']
    """
    return list(FACIAL_AXES.keys())


def get_facial_axis_values(axis: str) -> list[str]:
    """Get all possible values for a specific facial axis.

    Args:
        axis: Name of the axis (e.g., 'facial_signal')

    Returns:
        List of possible values for that axis

    Raises:
        KeyError: If axis is not defined in FACIAL_AXES

    Example:
        >>> get_facial_axis_values('facial_signal')
        ['understated', 'pronounced', 'exaggerated', 'asymmetrical',
         'weathered', 'soft-featured', 'sharp-featured']
    """
    return FACIAL_AXES[axis]


# ============================================================================
# MODULE METADATA
# ============================================================================

__all__ = [
    "FACIAL_AXES",
    "FACIAL_POLICY",
    "FACIAL_WEIGHTS",
    "FACIAL_EXCLUSIONS",
    "generate_facial_condition",
    "facial_condition_to_prompt",
    "get_available_facial_axes",
    "get_facial_axis_values",
]
