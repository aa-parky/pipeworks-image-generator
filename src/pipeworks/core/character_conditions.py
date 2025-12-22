"""Character condition generation system.

This module implements a structured, rule-based system for generating coherent
character state descriptions across multiple axes (physique, wealth, health, etc.).

Unlike simple text file lookups, this system uses:
- Weighted probability distributions for realistic populations
- Semantic exclusion rules to prevent illogical combinations
- Mandatory and optional axis policies to control complexity
- Reproducible generation via random seeds

The system is designed for procedural character generation in both visual
(image generation prompts) and narrative (MUD/game) contexts.

Example usage:
    >>> from pipeworks.core.character_conditions import generate_condition, condition_to_prompt
    >>> condition = generate_condition(seed=42)
    >>> prompt_fragment = condition_to_prompt(condition)
    >>> print(prompt_fragment)
    'skinny, poor, weary, alert'

Architecture:
    1. CONDITION_AXES: Define all possible values for each axis
    2. AXIS_POLICY: Rules for mandatory vs optional axes
    3. WEIGHTS: Statistical distribution for realistic populations
    4. EXCLUSIONS: Semantic constraints to prevent nonsense
    5. Generator: Produces constrained random combinations
    6. Converter: Transforms structured data into prompt text
"""

import logging
import random
from typing import Any

logger = logging.getLogger(__name__)

# ============================================================================
# AXIS DEFINITIONS - Single Source of Truth
# ============================================================================

CONDITION_AXES: dict[str, list[str]] = {
    # Physical build and body structure
    "physique": ["skinny", "wiry", "stocky", "hunched", "frail", "broad"],
    # Economic/social status indicators
    "wealth": ["poor", "modest", "well-kept", "wealthy", "decadent"],
    # Physical health and condition
    "health": ["sickly", "scarred", "weary", "hale", "limping"],
    # Behavioral presentation and attitude
    "demeanor": ["timid", "suspicious", "resentful", "alert", "proud"],
    # Life stage
    "age": ["young", "middle-aged", "old", "ancient"],
}

# ============================================================================
# AXIS POLICY - Controls Complexity and Prompt Clarity
# ============================================================================

AXIS_POLICY: dict[str, Any] = {
    # Always include these axes (establish baseline character state)
    "mandatory": ["physique", "wealth"],
    # May include 0-N of these axes (add narrative detail)
    "optional": ["health", "demeanor", "age"],
    # Maximum number of optional axes to include
    # (prevents prompt dilution and maintains diffusion model clarity)
    "max_optional": 2,
}

# ============================================================================
# WEIGHTS - Statistical Population Distribution
# ============================================================================

WEIGHTS: dict[str, dict[str, float]] = {
    # Wealth distribution: skewed toward lower classes (realistic population)
    "wealth": {
        "poor": 4.0,  # Most common
        "modest": 3.0,
        "well-kept": 2.0,
        "wealthy": 1.0,
        "decadent": 0.5,  # Rare
    },
    # Physique distribution: skewed toward survival builds
    "physique": {
        "skinny": 3.0,
        "wiry": 2.0,
        "hunched": 2.0,
        "frail": 1.0,
        "stocky": 1.0,
        "broad": 0.5,  # Rare
    },
    # Other axes use uniform distribution (no weights defined)
}

# ============================================================================
# EXCLUSIONS - Semantic Coherence Rules
# ============================================================================

EXCLUSIONS: dict[tuple[str, str], dict[str, list[str]]] = {
    # Decadent characters are unlikely to be frail or sickly
    # (wealth enables health care and nutrition)
    ("wealth", "decadent"): {
        "physique": ["frail"],
        "health": ["sickly"],
    },
    # Ancient characters aren't timid
    # (age brings confidence, even if it brings frailty)
    ("age", "ancient"): {
        "demeanor": ["timid"],
    },
    # Broad, strong physiques don't pair with sickness
    ("physique", "broad"): {
        "health": ["sickly"],
    },
    # Hale (healthy) characters shouldn't have frail physiques
    ("health", "hale"): {
        "physique": ["frail"],
    },
}


# ============================================================================
# GENERATOR FUNCTIONS
# ============================================================================


def weighted_choice(options: list[str], weights: dict[str, float] | None = None) -> str:
    """Select a random option with optional weighted probabilities.

    Args:
        options: List of possible values to choose from
        weights: Optional dictionary mapping options to weights.
                If None or missing entries, defaults to uniform distribution.

    Returns:
        Randomly selected option (str)

    Examples:
        >>> # Uniform distribution
        >>> weighted_choice(["a", "b", "c"])
        'b'

        >>> # Weighted distribution (more likely to pick "common")
        >>> weighted_choice(["rare", "common"], {"rare": 1, "common": 5})
        'common'
    """
    if not weights:
        return random.choice(options)

    # Build weight list matching option order
    # Use weight of 1.0 for any option not in the weights dict
    weight_values = [weights.get(option, 1.0) for option in options]

    # random.choices returns a list of k elements, we want just one
    return random.choices(options, weights=weight_values, k=1)[0]


def generate_condition(seed: int | None = None) -> dict[str, str]:
    """Generate a coherent character condition using weighted random selection.

    This function applies the full rule system:
    1. Select mandatory axes (always included)
    2. Select 0-N optional axes (controlled by policy)
    3. Apply weighted probability distributions
    4. Apply semantic exclusion rules
    5. Return structured condition data

    Args:
        seed: Optional random seed for reproducible generation.
             If None, uses system entropy (non-reproducible).

    Returns:
        Dictionary mapping axis names to selected values.
        Example: {"physique": "wiry", "wealth": "poor", "demeanor": "alert"}

    Examples:
        >>> # Reproducible generation
        >>> cond1 = generate_condition(seed=42)
        >>> cond2 = generate_condition(seed=42)
        >>> cond1 == cond2
        True

        >>> # Non-reproducible (different each call)
        >>> generate_condition()
        {'physique': 'stocky', 'wealth': 'modest', 'health': 'weary'}
    """
    # Set random seed for reproducibility if provided
    if seed is not None:
        random.seed(seed)

    chosen: dict[str, str] = {}

    # ========================================================================
    # PHASE 1: Select mandatory axes
    # These establish the baseline character state
    # ========================================================================
    for axis in AXIS_POLICY["mandatory"]:
        if axis not in CONDITION_AXES:
            logger.warning(f"Mandatory axis '{axis}' not defined in CONDITION_AXES")
            continue

        chosen[axis] = weighted_choice(CONDITION_AXES[axis], WEIGHTS.get(axis))
        logger.debug(f"Mandatory axis selected: {axis} = {chosen[axis]}")

    # ========================================================================
    # PHASE 2: Select optional axes
    # Randomly pick 0 to max_optional axes to add narrative detail
    # ========================================================================
    max_optional = AXIS_POLICY.get("max_optional", 2)
    num_optional = random.randint(0, min(max_optional, len(AXIS_POLICY["optional"])))

    # Randomly sample without replacement
    optional_axes = random.sample(AXIS_POLICY["optional"], num_optional)
    logger.debug(f"Selected {num_optional} optional axes: {optional_axes}")

    for axis in optional_axes:
        if axis not in CONDITION_AXES:
            logger.warning(f"Optional axis '{axis}' not defined in CONDITION_AXES")
            continue

        chosen[axis] = weighted_choice(CONDITION_AXES[axis], WEIGHTS.get(axis))
        logger.debug(f"Optional axis selected: {axis} = {chosen[axis]}")

    # ========================================================================
    # PHASE 3: Apply semantic exclusion rules
    # Remove illogical combinations (e.g., decadent + frail)
    # ========================================================================
    exclusions_applied = 0

    for (axis, value), blocked in EXCLUSIONS.items():
        # Check if this exclusion rule is triggered
        if chosen.get(axis) == value:
            logger.debug(f"Exclusion rule triggered: {axis}={value}")

            # Check each blocked axis
            for blocked_axis, blocked_values in blocked.items():
                if chosen.get(blocked_axis) in blocked_values:
                    removed_value = chosen.pop(blocked_axis)
                    exclusions_applied += 1
                    logger.debug(
                        f"  Removed {blocked_axis}={removed_value} "
                        f"(conflicts with {axis}={value})"
                    )

    if exclusions_applied > 0:
        logger.info(f"Applied {exclusions_applied} exclusion rule(s)")

    return chosen


def condition_to_prompt(condition_dict: dict[str, str]) -> str:
    """Convert structured condition data to a comma-separated prompt fragment.

    This is the only place structured data becomes prose text.
    The output is designed to be clean and diffusion-friendly.

    Args:
        condition_dict: Dictionary mapping axis names to values
                       (output from generate_condition)

    Returns:
        Comma-separated string of condition values

    Examples:
        >>> condition_to_prompt({"physique": "wiry", "wealth": "poor"})
        'wiry, poor'

        >>> condition_to_prompt({"physique": "stocky", "wealth": "modest", "age": "old"})
        'stocky, modest, old'

    Notes:
        - Order is determined by dict iteration (Python 3.7+ preserves insertion order)
        - If you need deterministic ordering, consider sorting by axis name
        - Empty dict returns empty string
    """
    if not condition_dict:
        return ""

    # Join values with comma separator (diffusion-friendly format)
    return ", ".join(condition_dict.values())


def get_available_axes() -> list[str]:
    """Get list of all defined condition axes.

    Returns:
        List of axis names (e.g., ['physique', 'wealth', 'health', ...])

    Example:
        >>> get_available_axes()
        ['physique', 'wealth', 'health', 'demeanor', 'age']
    """
    return list(CONDITION_AXES.keys())


def get_axis_values(axis: str) -> list[str]:
    """Get all possible values for a specific axis.

    Args:
        axis: Name of the axis (e.g., 'physique', 'wealth')

    Returns:
        List of possible values for that axis

    Raises:
        KeyError: If axis is not defined in CONDITION_AXES

    Example:
        >>> get_axis_values('wealth')
        ['poor', 'modest', 'well-kept', 'wealthy', 'decadent']
    """
    return CONDITION_AXES[axis]


# ============================================================================
# MODULE METADATA
# ============================================================================

__all__ = [
    "CONDITION_AXES",
    "AXIS_POLICY",
    "WEIGHTS",
    "EXCLUSIONS",
    "weighted_choice",
    "generate_condition",
    "condition_to_prompt",
    "get_available_axes",
    "get_axis_values",
]
