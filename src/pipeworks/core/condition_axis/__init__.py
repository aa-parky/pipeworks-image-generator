"""Condition axis generation system for procedural character and world building.

This package implements a structured, rule-based framework for generating coherent
state descriptions across multiple semantic dimensions (axes). It is designed for
use in both visual generation (image prompts) and narrative contexts (MUD/IF games).

The condition axis system provides:
- **Weighted probability distributions** for realistic populations
- **Semantic exclusion rules** to prevent illogical combinations
- **Mandatory and optional axis policies** to control complexity
- **Reproducible generation** via random seeds
- **Extensible architecture** for adding new condition types

Available Modules:
    - character_conditions: Physical and social character states
    - facial_conditions: Facial perception modifiers
    - _base: Shared utilities (internal)

Example usage:
    >>> from pipeworks.core.condition_axis import (
    ...     generate_condition,
    ...     generate_facial_condition,
    ...     condition_to_prompt,
    ... )
    >>>
    >>> # Generate character conditions
    >>> char = generate_condition(seed=42)
    >>> print(condition_to_prompt(char))
    'wiry, poor, weary'
    >>>
    >>> # Generate facial conditions
    >>> face = generate_facial_condition(seed=42)
    >>> print(facial_condition_to_prompt(face))
    'weathered'
    >>>
    >>> # Combine for complete character
    >>> full_prompt = f"{condition_to_prompt(char)}, {facial_condition_to_prompt(face)}"
    >>> print(full_prompt)
    'wiry, poor, weary, weathered'

For MUD/IF development, consider implementing a unified generator that applies
cross-system exclusion rules (e.g., age="young" conflicts with facial="weathered").
"""

# ============================================================================
# Character Conditions (Physical & Social States)
# ============================================================================

from .character_conditions import (
    AXIS_POLICY,
    CONDITION_AXES,
    EXCLUSIONS,
    WEIGHTS,
    condition_to_prompt,
    generate_condition,
    get_available_axes,
    get_axis_values,
)

# ============================================================================
# Facial Conditions (Facial Perception Modifiers)
# ============================================================================
from .facial_conditions import (
    FACIAL_AXES,
    FACIAL_EXCLUSIONS,
    FACIAL_POLICY,
    FACIAL_WEIGHTS,
    facial_condition_to_prompt,
    generate_facial_condition,
    get_available_facial_axes,
    get_facial_axis_values,
)

# ============================================================================
# Public API
# ============================================================================

__all__ = [
    # Character conditions
    "generate_condition",
    "condition_to_prompt",
    "CONDITION_AXES",
    "AXIS_POLICY",
    "WEIGHTS",
    "EXCLUSIONS",
    "get_available_axes",
    "get_axis_values",
    # Facial conditions
    "generate_facial_condition",
    "facial_condition_to_prompt",
    "FACIAL_AXES",
    "FACIAL_POLICY",
    "FACIAL_WEIGHTS",
    "FACIAL_EXCLUSIONS",
    "get_available_facial_axes",
    "get_facial_axis_values",
]

__version__ = "1.0.0"
