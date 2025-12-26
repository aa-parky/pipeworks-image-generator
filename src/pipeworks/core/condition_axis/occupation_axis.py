"""Occupation condition generation system for character and world building.

This module implements a structured system for generating occupation descriptors
across multiple semantic dimensions (legitimacy, visibility, moral weight, etc.).

Unlike simple occupation name lookups, this system generates the contextual
characteristics and social positioning of occupations, which can be combined
with character conditions to create rich, coherent character backgrounds.

Design Philosophy:
    Occupations are characterized by their relationship to society:
    - legitimacy: How society views the occupation legally/officially
    - visibility: How conspicuous the occupation is in daily life
    - moral_load: The psychological/ethical weight carried by practitioners
    - dependency: How essential the occupation is to society
    - risk_exposure: Physical/psychological toll over time

Example usage:
    >>> from pipeworks.core.condition_axis import generate_occupation_condition
    >>> occupation = generate_occupation_condition(seed=42)
    >>> print(occupation)
    {'legitimacy': 'tolerated', 'visibility': 'discreet', 'moral_load': 'burdened'}

    >>> from pipeworks.core.condition_axis import occupation_condition_to_prompt
    >>> prompt_fragment = occupation_condition_to_prompt(occupation)
    >>> print(prompt_fragment)
    'tolerated, discreet, burdened'

Architecture:
    1. OCCUPATION_AXES: Define all possible values for each axis
    2. OCCUPATION_POLICY: Rules for mandatory vs optional axes
    3. OCCUPATION_WEIGHTS: Statistical distribution for realistic variety
    4. OCCUPATION_EXCLUSIONS: Semantic constraints for coherence
    5. Generator: Produces constrained random combinations
    6. Converter: Transforms structured data into prompt text

Future Integration:
    This module can be combined with character_conditions and facial_conditions
    to create complete character profiles. Cross-system exclusions may be needed:
    - wealth="decadent" + legitimacy="illicit" (criminal wealth sources)
    - age="young" + dependency="unavoidable" (unlikely to hold critical roles)
    - demeanor="timid" + visibility="conspicuous" (contradictory behavior)
"""

import logging
import random
from typing import Any

from ._base import apply_exclusion_rules, values_to_prompt, weighted_choice

logger = logging.getLogger(__name__)

# ============================================================================
# AXIS DEFINITIONS - Single Source of Truth for Occupation Characteristics
# ============================================================================

OCCUPATION_AXES: dict[str, list[str]] = {
    # Legal/social legitimacy of the occupation
    "legitimacy": [
        "sanctioned",  # Officially approved, licensed, regulated
        "tolerated",  # Accepted but not formally regulated
        "questioned",  # Legal but socially/ethically dubious
        "illicit",  # Illegal or forbidden
    ],
    # Public visibility and conspicuousness
    "visibility": [
        "hidden",  # Deliberately concealed from public view
        "discreet",  # Low-profile, not advertised
        "routine",  # Normal, unremarkable presence
        "conspicuous",  # Highly visible, attention-drawing
    ],
    # Psychological/ethical burden on practitioners
    "moral_load": [
        "neutral",  # No significant moral weight
        "burdened",  # Some ethical weight or moral questioning
        "conflicted",  # Ongoing moral struggle or doubt
        "corrosive",  # Soul-destroying, psychologically damaging
    ],
    # Societal dependence on the occupation
    "dependency": [
        "optional",  # Nice to have, luxury service
        "useful",  # Beneficial but not critical
        "necessary",  # Important for normal functioning
        "unavoidable",  # Society cannot function without it
    ],
    # Physical/psychological risk and toll over time
    "risk_exposure": [
        "benign",  # Safe, minimal long-term impact
        "straining",  # Demanding but manageable
        "hazardous",  # Significant risk of injury/harm
        "eroding",  # Gradual degradation of health/sanity
    ],
}

# ============================================================================
# AXIS POLICY - Controls Occupation Complexity
# ============================================================================

OCCUPATION_POLICY: dict[str, Any] = {
    # Always include these axes (establish baseline occupation profile)
    "mandatory": ["legitimacy", "visibility"],
    # May include 0-N of these axes (add contextual detail)
    "optional": ["moral_load", "dependency", "risk_exposure"],
    # Maximum number of optional axes to include
    # (prevents prompt dilution and maintains clarity)
    "max_optional": 2,
}

# ============================================================================
# WEIGHTS - Statistical Distribution for Realistic Variety
# ============================================================================

OCCUPATION_WEIGHTS: dict[str, dict[str, float]] = {
    # Legitimacy distribution: Most work is legal
    "legitimacy": {
        "sanctioned": 4.0,  # Most common (licensed professions)
        "tolerated": 3.0,  # Common (informal economy)
        "questioned": 1.5,  # Less common (grey areas)
        "illicit": 0.5,  # Rare (criminal enterprises)
    },
    # Visibility distribution: Most work is routine or discreet
    "visibility": {
        "routine": 4.0,  # Most common (everyday jobs)
        "discreet": 3.0,  # Common (behind-the-scenes work)
        "hidden": 1.0,  # Uncommon (secret operations)
        "conspicuous": 1.0,  # Uncommon (public performances)
    },
    # Moral load distribution: Most work is neutral
    "moral_load": {
        "neutral": 5.0,  # Most common
        "burdened": 2.0,  # Less common
        "conflicted": 1.0,  # Uncommon
        "corrosive": 0.5,  # Rare
    },
    # Dependency distribution: Skewed toward useful/necessary
    "dependency": {
        "necessary": 3.0,  # Common (essential services)
        "useful": 3.0,  # Common (beneficial services)
        "optional": 2.0,  # Less common (luxury services)
        "unavoidable": 1.0,  # Uncommon (critical infrastructure)
    },
    # Risk exposure distribution: Most work is safe
    "risk_exposure": {
        "benign": 4.0,  # Most common (desk jobs, safe work)
        "straining": 3.0,  # Common (physically demanding)
        "hazardous": 1.5,  # Less common (dangerous work)
        "eroding": 0.5,  # Rare (soul-crushing or health-destroying)
    },
}

# ============================================================================
# EXCLUSIONS - Semantic Coherence Rules
# ============================================================================

OCCUPATION_EXCLUSIONS: dict[tuple[str, str], dict[str, list[str]]] = {
    # Note: Bidirectional exclusions between mandatory axes (legitimacy + visibility)
    # These rules must work in both directions to prevent removing mandatory axes
    # Illicit occupations avoid conspicuous visibility
    # (criminals don't advertise their illegal activities)
    ("legitimacy", "illicit"): {
        "visibility": ["conspicuous"],
    },
    # Conspicuous visibility excludes illicit legitimacy
    # (reinforces the rule from the opposite direction)
    ("visibility", "conspicuous"): {
        "legitimacy": ["illicit"],
    },
    # Sanctioned occupations aren't hidden
    # (why conceal legal, approved work?)
    ("legitimacy", "sanctioned"): {
        "visibility": ["hidden"],
    },
    # Hidden visibility excludes sanctioned legitimacy
    # (reinforces the rule from the opposite direction)
    ("visibility", "hidden"): {
        "legitimacy": ["sanctioned"],
        # Hidden occupations can't be unavoidable dependencies
        # (critical infrastructure must be visible/accessible)
        "dependency": ["unavoidable"],
    },
    # Eroding risk exposure carries moral weight
    # (long-term health/sanity damage isn't morally neutral)
    ("risk_exposure", "eroding"): {
        "moral_load": ["neutral"],
    },
    # Optional work shouldn't be eroding
    # (why do soul-crushing work that's not necessary?)
    # Note: This is conservative - some people do take optional risky work
    # (extreme sports, dangerous hobbies), but in occupation context it's uncommon
    ("dependency", "optional"): {
        "risk_exposure": ["eroding"],
    },
}


# ============================================================================
# GENERATOR FUNCTIONS
# ============================================================================


def generate_occupation_condition(seed: int | None = None) -> dict[str, str]:
    """Generate a coherent occupation condition using weighted random selection.

    This function applies the full occupation rule system:
    1. Select mandatory axes (legitimacy, visibility)
    2. Select 0-N optional axes (moral_load, dependency, risk_exposure)
    3. Apply weighted probability distributions
    4. Apply semantic exclusion rules
    5. Return structured condition data

    Args:
        seed: Optional random seed for reproducible generation.
             If None, uses system entropy (non-reproducible).

    Returns:
        Dictionary mapping axis names to selected values.
        Example: {"legitimacy": "tolerated", "visibility": "discreet",
                 "moral_load": "burdened"}

    Examples:
        >>> # Reproducible generation
        >>> occ1 = generate_occupation_condition(seed=42)
        >>> occ2 = generate_occupation_condition(seed=42)
        >>> occ1 == occ2
        True

        >>> # Non-reproducible (different each call)
        >>> generate_occupation_condition()
        {'legitimacy': 'sanctioned', 'visibility': 'routine', 'dependency': 'useful'}

        >>> # May include 0-2 optional axes
        >>> generate_occupation_condition(seed=100)
        {'legitimacy': 'tolerated', 'visibility': 'discreet'}
    """
    # Set random seed for reproducibility if provided
    if seed is not None:
        random.seed(seed)

    chosen: dict[str, str] = {}

    # ========================================================================
    # PHASE 1: Select mandatory axes
    # These establish the baseline occupation profile
    # ========================================================================
    for axis in OCCUPATION_POLICY["mandatory"]:
        if axis not in OCCUPATION_AXES:
            logger.warning(f"Mandatory axis '{axis}' not defined in OCCUPATION_AXES")
            continue

        chosen[axis] = weighted_choice(OCCUPATION_AXES[axis], OCCUPATION_WEIGHTS.get(axis))
        logger.debug(f"Mandatory axis selected: {axis} = {chosen[axis]}")

    # ========================================================================
    # PHASE 2: Select optional axes
    # Randomly pick 0 to max_optional axes to add contextual detail
    # ========================================================================
    max_optional = OCCUPATION_POLICY.get("max_optional", 2)
    num_optional = random.randint(0, min(max_optional, len(OCCUPATION_POLICY["optional"])))

    # Randomly sample without replacement
    optional_axes = random.sample(OCCUPATION_POLICY["optional"], num_optional)
    logger.debug(f"Selected {num_optional} optional axes: {optional_axes}")

    for axis in optional_axes:
        if axis not in OCCUPATION_AXES:
            logger.warning(f"Optional axis '{axis}' not defined in OCCUPATION_AXES")
            continue

        chosen[axis] = weighted_choice(OCCUPATION_AXES[axis], OCCUPATION_WEIGHTS.get(axis))
        logger.debug(f"Optional axis selected: {axis} = {chosen[axis]}")

    # ========================================================================
    # PHASE 3: Apply semantic exclusion rules
    # Remove illogical combinations (e.g., illicit + conspicuous)
    # ========================================================================
    apply_exclusion_rules(chosen, OCCUPATION_EXCLUSIONS)

    return chosen


def occupation_condition_to_prompt(condition_dict: dict[str, str]) -> str:
    """Convert structured occupation condition data to a prompt fragment.

    This is the canonical serialization format for occupation axis data.
    The output is designed to be clean and diffusion-friendly.

    Args:
        condition_dict: Dictionary mapping axis names to values
                       (output from generate_occupation_condition)

    Returns:
        Comma-separated string of condition values

    Examples:
        >>> occupation_condition_to_prompt({"legitimacy": "tolerated", "visibility": "discreet"})
        'tolerated, discreet'

        >>> occupation_condition_to_prompt({
        ...     "legitimacy": "sanctioned",
        ...     "visibility": "routine",
        ...     "dependency": "necessary"
        ... })
        'sanctioned, routine, necessary'

        >>> occupation_condition_to_prompt({})
        ''

    Notes:
        - Order is determined by dict iteration (Python 3.7+ preserves insertion order)
        - Only includes values, not axis names (for prompt clarity)
        - Empty dict returns empty string
    """
    return values_to_prompt(condition_dict)


def get_available_occupation_axes() -> list[str]:
    """Get list of all defined occupation condition axes.

    Returns:
        List of axis names (e.g., ['legitimacy', 'visibility', ...])

    Example:
        >>> get_available_occupation_axes()
        ['legitimacy', 'visibility', 'moral_load', 'dependency', 'risk_exposure']
    """
    return list(OCCUPATION_AXES.keys())


def get_occupation_axis_values(axis: str) -> list[str]:
    """Get all possible values for a specific occupation axis.

    Args:
        axis: Name of the axis (e.g., 'legitimacy', 'visibility')

    Returns:
        List of possible values for that axis

    Raises:
        KeyError: If axis is not defined in OCCUPATION_AXES

    Example:
        >>> get_occupation_axis_values('legitimacy')
        ['sanctioned', 'tolerated', 'questioned', 'illicit']

        >>> get_occupation_axis_values('moral_load')
        ['neutral', 'burdened', 'conflicted', 'corrosive']
    """
    return OCCUPATION_AXES[axis]


# ============================================================================
# MODULE METADATA
# ============================================================================

__all__ = [
    "OCCUPATION_AXES",
    "OCCUPATION_POLICY",
    "OCCUPATION_WEIGHTS",
    "OCCUPATION_EXCLUSIONS",
    "generate_occupation_condition",
    "occupation_condition_to_prompt",
    "get_available_occupation_axes",
    "get_occupation_axis_values",
]
