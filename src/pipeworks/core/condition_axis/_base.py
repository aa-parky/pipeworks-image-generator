"""Shared utilities for condition axis generation system.

This module provides common functionality used by all condition axis generators
(character, facial, occupation, etc.) to maintain consistency and reduce code
duplication.

The condition axis system is a structured, rule-based framework for generating
coherent state descriptions across multiple dimensions. It is used for:
- Procedural character generation (MUD/IF games)
- Image generation prompt construction
- Narrative content generation

Core concepts:
- **Axes**: Semantic dimensions with discrete values (e.g., physique: skinny, wiry, stocky)
- **Weights**: Probability distributions for realistic populations
- **Exclusions**: Semantic constraints to prevent illogical combinations
- **Policy**: Rules for mandatory vs. optional axes
"""

import logging
import random

logger = logging.getLogger(__name__)


def weighted_choice(options: list[str], weights: dict[str, float] | None = None) -> str:
    """Select a random option with optional weighted probabilities.

    This is the core selection mechanism for all condition axis generators.
    It enables both uniform and weighted probability distributions, allowing
    for realistic population modeling (e.g., "poor" is more common than "wealthy").

    Args:
        options: List of possible values to choose from.
                Must be non-empty.
        weights: Optional dictionary mapping options to weights.
                If None or missing entries, defaults to uniform distribution.
                Weights must be non-negative (zero weight = never selected).

    Returns:
        Randomly selected option (str)

    Examples:
        >>> # Uniform distribution (all equally likely)
        >>> weighted_choice(["a", "b", "c"])
        'b'

        >>> # Weighted distribution (biased toward common values)
        >>> weighted_choice(["rare", "common"], {"rare": 1.0, "common": 5.0})
        'common'

        >>> # Partial weights (missing options default to 1.0)
        >>> weighted_choice(["a", "b", "c"], {"a": 3.0})  # a=3.0, b=1.0, c=1.0
        'a'

    Notes:
        - Uses random.choices() for weighted selection
        - Falls back to random.choice() for uniform distribution (performance)
        - Thread-safety depends on Python's random module (thread-local RNG)
    """
    if not weights:
        # Fast path: uniform distribution
        return random.choice(options)

    # Build weight list matching option order
    # Use weight of 1.0 for any option not in the weights dict
    weight_values = [weights.get(option, 1.0) for option in options]

    # random.choices returns a list of k elements, we want just one
    return random.choices(options, weights=weight_values, k=1)[0]


def apply_exclusion_rules(
    chosen: dict[str, str],
    exclusions: dict[tuple[str, str], dict[str, list[str]]],
) -> dict[str, str]:
    """Apply semantic exclusion rules to remove illogical combinations.

    Exclusion rules encode domain knowledge about incompatible combinations.
    For example: "wealthy + frail" is unlikely (wealth enables health care),
    or "ancient + timid" is incoherent (age brings confidence).

    Args:
        chosen: Dictionary mapping axis names to selected values.
               Modified in-place as exclusions are applied.
        exclusions: Dictionary of exclusion rules.
                   Format: {(axis, value): {blocked_axis: [blocked_values]}}
                   Example: {("wealth", "decadent"): {"health": ["sickly"]}}

    Returns:
        The modified chosen dictionary (same reference, for convenience)

    Examples:
        >>> chosen = {"wealth": "decadent", "health": "sickly"}
        >>> exclusions = {("wealth", "decadent"): {"health": ["sickly"]}}
        >>> apply_exclusion_rules(chosen, exclusions)
        {'wealth': 'decadent'}  # health removed due to conflict

        >>> chosen = {"age": "young", "demeanor": "alert"}
        >>> exclusions = {("age", "ancient"): {"demeanor": ["timid"]}}
        >>> apply_exclusion_rules(chosen, exclusions)
        {'age': 'young', 'demeanor': 'alert'}  # no exclusion triggered

    Notes:
        - Modifies the chosen dict in-place
        - Logs all applied exclusions at DEBUG level
        - Returns the same dict reference for chaining
        - Removal order is deterministic (dict iteration order)
    """
    exclusions_applied = 0

    for (axis, value), blocked in exclusions.items():
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


def values_to_prompt(condition_dict: dict[str, str]) -> str:
    """Convert structured condition data to a comma-separated prompt fragment.

    This is the canonical serialization format for condition axis data.
    The output is designed to be:
    - Human-readable
    - Diffusion model friendly (comma-separated keywords)
    - Consistent across all condition axis types

    Args:
        condition_dict: Dictionary mapping axis names to values
                       (output from any generate_* function)

    Returns:
        Comma-separated string of condition values.
        Order is deterministic (Python 3.7+ dict insertion order).
        Empty dict returns empty string.

    Examples:
        >>> values_to_prompt({"physique": "wiry", "wealth": "poor"})
        'wiry, poor'

        >>> values_to_prompt({"physique": "stocky", "wealth": "modest", "age": "old"})
        'stocky, modest, old'

        >>> values_to_prompt({})
        ''

    Notes:
        - Only includes values, not axis names (for prompt clarity)
        - Maintains insertion order from generation
        - Can be extended for different output formats (JSON, prose, etc.)
    """
    if not condition_dict:
        return ""

    # Join values with comma separator (diffusion-friendly format)
    return ", ".join(condition_dict.values())


__all__ = [
    "weighted_choice",
    "apply_exclusion_rules",
    "values_to_prompt",
]
