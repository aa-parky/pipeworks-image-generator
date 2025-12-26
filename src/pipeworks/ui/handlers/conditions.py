"""Condition generation handlers for character, facial, and occupation conditions.

This module provides handlers for generating conditions in the Gradio UI. It supports:
- Character conditions (physique, wealth, health, demeanor, age)
- Facial conditions (facial signals like weathered, sharp-featured, etc.)
- Occupation conditions (legitimacy, visibility, moral load, dependency, risk)
- Combined conditions (character + facial, or all three)

The handlers are used in the UI to respond to dropdown changes and regenerate
button clicks in Start 2 and Start 3 segments.
"""

import logging

logger = logging.getLogger(__name__)


def generate_condition_by_type(condition_type: str, seed: int | None = None) -> str:
    """Generate condition text based on the selected condition type.

    This is the main entry point for condition generation. It routes to the
    appropriate generator based on the condition_type parameter.

    Args:
        condition_type: Type of condition to generate.
                       Must be one of: "None", "Character", "Facial", "Occupation",
                       "Both" (Character + Facial), or "All" (all three)
        seed: Optional random seed for reproducible generation.
             If None, uses system entropy (non-reproducible).

    Returns:
        Generated condition text as a comma-separated string.
        Returns empty string if condition_type is "None".

    Examples:
        >>> generate_condition_by_type("Character", seed=42)
        'wiry, modest, old'

        >>> generate_condition_by_type("Facial", seed=42)
        'weathered'

        >>> generate_condition_by_type("Occupation", seed=42)
        'tolerated, discreet, burdened'

        >>> generate_condition_by_type("Both", seed=42)
        'wiry, modest, old, weathered'

        >>> generate_condition_by_type("All", seed=42)
        'wiry, modest, old, weathered, tolerated, discreet'

        >>> generate_condition_by_type("None")
        ''
    """
    if condition_type == "None":
        return ""

    elif condition_type == "Character":
        return _generate_character_condition(seed)

    elif condition_type == "Facial":
        return _generate_facial_condition(seed)

    elif condition_type == "Occupation":
        return _generate_occupation_condition(seed)

    elif condition_type == "Both":
        return _generate_both_conditions(seed)

    elif condition_type == "All":
        return _generate_all_conditions(seed)

    else:
        logger.warning(f"Unknown condition type: {condition_type}")
        return ""


def _generate_character_condition(seed: int | None = None) -> str:
    """Generate character condition text.

    Args:
        seed: Optional random seed for reproducible generation

    Returns:
        Comma-separated character condition text
        Example: "wiry, modest, old"
    """
    from pipeworks.core.condition_axis import condition_to_prompt, generate_condition

    condition = generate_condition(seed=seed)
    return condition_to_prompt(condition)


def _generate_facial_condition(seed: int | None = None) -> str:
    """Generate facial condition text.

    Args:
        seed: Optional random seed for reproducible generation

    Returns:
        Facial condition text (single value or empty)
        Example: "weathered" or ""
    """
    from pipeworks.core.condition_axis import (
        facial_condition_to_prompt,
        generate_facial_condition,
    )

    condition = generate_facial_condition(seed=seed)
    return facial_condition_to_prompt(condition)


def _generate_occupation_condition(seed: int | None = None) -> str:
    """Generate occupation condition text.

    Args:
        seed: Optional random seed for reproducible generation

    Returns:
        Comma-separated occupation condition text
        Example: "tolerated, discreet, burdened"
    """
    from pipeworks.core.condition_axis import (
        generate_occupation_condition,
        occupation_condition_to_prompt,
    )

    condition = generate_occupation_condition(seed=seed)
    return occupation_condition_to_prompt(condition)


def _generate_both_conditions(seed: int | None = None) -> str:
    """Generate both character and facial conditions.

    The two conditions are generated using the same seed to maintain
    reproducibility. If a seed is provided, facial uses seed+1 to ensure
    different but deterministic results.

    Args:
        seed: Optional random seed for reproducible generation

    Returns:
        Comma-separated combination of character and facial conditions
        Example: "wiry, modest, old, weathered"
        Or: "wiry, modest, old" (if no facial condition generated)
    """
    # Generate character condition
    character_text = _generate_character_condition(seed)

    # Generate facial condition with offset seed if seed is provided
    # This ensures reproducibility while avoiding duplicate random states
    facial_seed = None if seed is None else seed + 1
    facial_text = _generate_facial_condition(facial_seed)

    # Combine conditions
    if character_text and facial_text:
        return f"{character_text}, {facial_text}"
    elif character_text:
        return character_text
    elif facial_text:
        return facial_text
    else:
        return ""


def _generate_all_conditions(seed: int | None = None) -> str:
    """Generate character, facial, and occupation conditions.

    All three conditions are generated using offset seeds to maintain
    reproducibility while ensuring different but deterministic results.

    Args:
        seed: Optional random seed for reproducible generation

    Returns:
        Comma-separated combination of all three condition types
        Example: "wiry, modest, old, weathered, tolerated, discreet"
    """
    # Generate all three condition types with offset seeds
    character_text = _generate_character_condition(seed)
    facial_seed = None if seed is None else seed + 1
    facial_text = _generate_facial_condition(facial_seed)
    occupation_seed = None if seed is None else seed + 2
    occupation_text = _generate_occupation_condition(occupation_seed)

    # Combine all non-empty conditions
    parts = []
    if character_text:
        parts.append(character_text)
    if facial_text:
        parts.append(facial_text)
    if occupation_text:
        parts.append(occupation_text)

    return ", ".join(parts)


__all__ = [
    "generate_condition_by_type",
]
