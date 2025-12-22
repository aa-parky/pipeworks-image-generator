"""Unit tests for character condition generation system.

This module tests the character_conditions module which implements
a structured, rule-based system for generating coherent character states.

Test coverage includes:
- Weighted random selection
- Condition generation with mandatory/optional axes
- Semantic exclusion rules
- Reproducibility via seeding
- Prompt text formatting
- Helper functions
"""

import random

import pytest

from pipeworks.core.character_conditions import (
    AXIS_POLICY,
    CONDITION_AXES,
    EXCLUSIONS,
    WEIGHTS,
    condition_to_prompt,
    generate_condition,
    get_available_axes,
    get_axis_values,
    weighted_choice,
)


# ============================================================================
# Test Data Structures
# ============================================================================


class TestDataStructures:
    """Test that data structures are well-formed and valid."""

    def test_condition_axes_structure(self):
        """Test CONDITION_AXES has expected structure."""
        assert isinstance(CONDITION_AXES, dict)
        assert len(CONDITION_AXES) > 0

        # All axes should have non-empty value lists
        for axis, values in CONDITION_AXES.items():
            assert isinstance(axis, str)
            assert isinstance(values, list)
            assert len(values) > 0
            # All values should be strings
            assert all(isinstance(v, str) for v in values)

    def test_axis_policy_structure(self):
        """Test AXIS_POLICY has expected structure."""
        assert isinstance(AXIS_POLICY, dict)
        assert "mandatory" in AXIS_POLICY
        assert "optional" in AXIS_POLICY
        assert "max_optional" in AXIS_POLICY

        # Mandatory and optional should be lists
        assert isinstance(AXIS_POLICY["mandatory"], list)
        assert isinstance(AXIS_POLICY["optional"], list)
        assert isinstance(AXIS_POLICY["max_optional"], int)

        # max_optional should be reasonable
        assert AXIS_POLICY["max_optional"] > 0
        assert AXIS_POLICY["max_optional"] <= len(AXIS_POLICY["optional"])

    def test_axis_policy_references_valid_axes(self):
        """Test that AXIS_POLICY only references defined axes."""
        all_policy_axes = AXIS_POLICY["mandatory"] + AXIS_POLICY["optional"]

        for axis in all_policy_axes:
            assert axis in CONDITION_AXES, f"Axis '{axis}' in policy but not in CONDITION_AXES"

    def test_no_overlap_mandatory_optional(self):
        """Test that mandatory and optional axes don't overlap."""
        mandatory_set = set(AXIS_POLICY["mandatory"])
        optional_set = set(AXIS_POLICY["optional"])

        overlap = mandatory_set & optional_set
        assert len(overlap) == 0, f"Axes appear in both mandatory and optional: {overlap}"

    def test_weights_structure(self):
        """Test WEIGHTS has expected structure."""
        assert isinstance(WEIGHTS, dict)

        for axis, weight_dict in WEIGHTS.items():
            assert axis in CONDITION_AXES, f"Weighted axis '{axis}' not in CONDITION_AXES"
            assert isinstance(weight_dict, dict)

            # All weighted values should exist in the axis
            for value, weight in weight_dict.items():
                assert (
                    value in CONDITION_AXES[axis]
                ), f"Weighted value '{value}' not in axis '{axis}'"
                assert isinstance(weight, (int, float))
                assert weight > 0, f"Weight for {axis}.{value} must be positive"

    def test_exclusions_structure(self):
        """Test EXCLUSIONS has expected structure."""
        assert isinstance(EXCLUSIONS, dict)

        for (axis, value), blocked in EXCLUSIONS.items():
            # Trigger axis/value should exist
            assert axis in CONDITION_AXES, f"Exclusion trigger axis '{axis}' not defined"
            assert (
                value in CONDITION_AXES[axis]
            ), f"Exclusion trigger value '{value}' not in axis '{axis}'"

            # Blocked axes/values should exist
            assert isinstance(blocked, dict)
            for blocked_axis, blocked_values in blocked.items():
                assert (
                    blocked_axis in CONDITION_AXES
                ), f"Blocked axis '{blocked_axis}' not defined"
                for blocked_value in blocked_values:
                    assert (
                        blocked_value in CONDITION_AXES[blocked_axis]
                    ), f"Blocked value '{blocked_value}' not in axis '{blocked_axis}'"


# ============================================================================
# Test weighted_choice Function
# ============================================================================


class TestWeightedChoice:
    """Test weighted random selection function."""

    def test_weighted_choice_uniform(self):
        """Test that weighted_choice works with no weights (uniform distribution)."""
        options = ["a", "b", "c"]

        # Run multiple times to ensure we get valid results
        for _ in range(10):
            result = weighted_choice(options)
            assert result in options

    def test_weighted_choice_with_weights(self):
        """Test that weighted_choice respects probability weights."""
        options = ["rare", "common"]
        weights = {"rare": 1, "common": 100}  # Common should be much more likely

        # Run many iterations and check distribution
        results = [weighted_choice(options, weights) for _ in range(1000)]

        # Should get mostly "common" results
        common_count = results.count("common")
        assert common_count > 900, "Expected ~99% common results"

    def test_weighted_choice_missing_weight(self):
        """Test that weighted_choice handles missing weights (defaults to 1.0)."""
        options = ["a", "b", "c"]
        weights = {"a": 5}  # Only 'a' has weight, b and c should default to 1.0

        # Run multiple times to ensure all options are possible
        results = [weighted_choice(options, weights) for _ in range(100)]

        # All options should appear (though 'a' should be more common)
        assert "a" in results
        assert "b" in results or "c" in results  # At least one of the non-weighted

    def test_weighted_choice_deterministic_with_seed(self):
        """Test that weighted_choice is reproducible with random seed."""
        options = ["a", "b", "c"]
        weights = {"a": 1, "b": 2, "c": 3}

        random.seed(42)
        result1 = weighted_choice(options, weights)

        random.seed(42)
        result2 = weighted_choice(options, weights)

        assert result1 == result2


# ============================================================================
# Test generate_condition Function
# ============================================================================


class TestGenerateCondition:
    """Test main condition generation function."""

    def test_generate_condition_returns_dict(self):
        """Test that generate_condition returns a dictionary."""
        result = generate_condition(seed=42)
        assert isinstance(result, dict)

    def test_generate_condition_includes_mandatory_axes(self):
        """Test that all mandatory axes are included."""
        result = generate_condition(seed=42)

        for axis in AXIS_POLICY["mandatory"]:
            assert axis in result, f"Mandatory axis '{axis}' not in result"
            assert result[axis] in CONDITION_AXES[axis]

    def test_generate_condition_respects_max_optional(self):
        """Test that number of optional axes respects max_optional limit."""
        # Run multiple times to test different random outcomes
        for seed in range(20):
            result = generate_condition(seed=seed)

            optional_count = sum(1 for axis in AXIS_POLICY["optional"] if axis in result)

            max_optional = AXIS_POLICY["max_optional"]
            assert (
                optional_count <= max_optional
            ), f"Too many optional axes: {optional_count} > {max_optional}"

    def test_generate_condition_all_values_valid(self):
        """Test that all selected values are valid for their axes."""
        for seed in range(10):
            result = generate_condition(seed=seed)

            for axis, value in result.items():
                assert axis in CONDITION_AXES, f"Invalid axis '{axis}' in result"
                assert (
                    value in CONDITION_AXES[axis]
                ), f"Invalid value '{value}' for axis '{axis}'"

    def test_generate_condition_reproducible_with_seed(self):
        """Test that same seed produces same condition."""
        result1 = generate_condition(seed=42)
        result2 = generate_condition(seed=42)

        assert result1 == result2

    def test_generate_condition_different_without_seed(self):
        """Test that conditions vary without seed (statistical test)."""
        # Generate many conditions and check for variation
        results = [generate_condition() for _ in range(20)]

        # Convert to tuples for set comparison
        result_tuples = [tuple(sorted(r.items())) for r in results]

        # Should have at least some variation (not all identical)
        unique_results = len(set(result_tuples))
        assert unique_results > 1, "All conditions were identical (very unlikely without seed)"

    def test_generate_condition_applies_exclusions(self):
        """Test that exclusion rules are applied correctly."""
        # This is a statistical test - run many generations and check exclusions
        violations = []

        for seed in range(100):
            result = generate_condition(seed=seed)

            # Check each exclusion rule
            for (axis, value), blocked in EXCLUSIONS.items():
                if result.get(axis) == value:
                    # This exclusion is triggered
                    for blocked_axis, blocked_values in blocked.items():
                        if result.get(blocked_axis) in blocked_values:
                            violations.append(
                                f"Seed {seed}: {axis}={value} conflicts with "
                                f"{blocked_axis}={result[blocked_axis]}"
                            )

        assert len(violations) == 0, f"Exclusion violations: {violations}"

    def test_generate_condition_handles_none_seed(self):
        """Test that generate_condition works with seed=None (non-reproducible)."""
        result = generate_condition(seed=None)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_generate_condition_weighted_distribution(self):
        """Test that weights affect probability distribution (statistical test)."""
        # Focus on wealth axis which has strong weights
        wealth_counts = {}

        for seed in range(500):
            result = generate_condition(seed=seed)
            if "wealth" in result:
                wealth = result["wealth"]
                wealth_counts[wealth] = wealth_counts.get(wealth, 0) + 1

        # "poor" should be most common (weight=4), "decadent" should be rarest (weight=0.5)
        if wealth_counts:
            most_common = max(wealth_counts, key=wealth_counts.get)
            least_common = min(wealth_counts, key=wealth_counts.get)

            # Statistical assertion: poor should appear more than decadent
            if "poor" in wealth_counts and "decadent" in wealth_counts:
                assert wealth_counts["poor"] > wealth_counts["decadent"]


# ============================================================================
# Test condition_to_prompt Function
# ============================================================================


class TestConditionToPrompt:
    """Test prompt text generation function."""

    def test_condition_to_prompt_basic(self):
        """Test basic prompt text generation."""
        condition = {"physique": "wiry", "wealth": "poor"}
        result = condition_to_prompt(condition)

        assert isinstance(result, str)
        assert "wiry" in result
        assert "poor" in result
        assert ", " in result  # Comma-separated

    def test_condition_to_prompt_empty(self):
        """Test prompt generation with empty condition."""
        result = condition_to_prompt({})
        assert result == ""

    def test_condition_to_prompt_single_axis(self):
        """Test prompt generation with single axis."""
        condition = {"physique": "stocky"}
        result = condition_to_prompt(condition)

        assert result == "stocky"

    def test_condition_to_prompt_multiple_axes(self):
        """Test prompt generation with multiple axes."""
        condition = {"physique": "wiry", "wealth": "poor", "demeanor": "alert"}
        result = condition_to_prompt(condition)

        # Should be comma-separated
        parts = result.split(", ")
        assert len(parts) == 3
        assert "wiry" in parts
        assert "poor" in parts
        assert "alert" in parts

    def test_condition_to_prompt_integration(self):
        """Test prompt generation from generated condition."""
        condition = generate_condition(seed=42)
        result = condition_to_prompt(condition)

        assert isinstance(result, str)
        assert len(result) > 0
        # Should have commas (multiple axes)
        assert ", " in result or len(condition) == 1


# ============================================================================
# Test Helper Functions
# ============================================================================


class TestHelperFunctions:
    """Test utility and helper functions."""

    def test_get_available_axes(self):
        """Test get_available_axes returns all axes."""
        axes = get_available_axes()

        assert isinstance(axes, list)
        assert len(axes) == len(CONDITION_AXES)

        # All axes should be present
        for axis in CONDITION_AXES:
            assert axis in axes

    def test_get_axis_values(self):
        """Test get_axis_values returns correct values."""
        for axis in CONDITION_AXES:
            values = get_axis_values(axis)

            assert isinstance(values, list)
            assert values == CONDITION_AXES[axis]

    def test_get_axis_values_invalid_axis(self):
        """Test get_axis_values raises error for invalid axis."""
        with pytest.raises(KeyError):
            get_axis_values("nonexistent_axis")


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Test full workflow integration."""

    def test_full_generation_workflow(self):
        """Test complete workflow: generate -> convert -> use."""
        # Step 1: Generate condition
        condition = generate_condition(seed=42)
        assert isinstance(condition, dict)
        assert len(condition) > 0

        # Step 2: Convert to prompt
        prompt = condition_to_prompt(condition)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

        # Step 3: Verify all condition values are in prompt
        for value in condition.values():
            assert value in prompt

    def test_reproducible_workflow(self):
        """Test that entire workflow is reproducible with seed."""
        # Run 1
        condition1 = generate_condition(seed=12345)
        prompt1 = condition_to_prompt(condition1)

        # Run 2
        condition2 = generate_condition(seed=12345)
        prompt2 = condition_to_prompt(condition2)

        assert condition1 == condition2
        assert prompt1 == prompt2

    def test_multiple_generations_diversity(self):
        """Test that multiple generations produce diverse results."""
        prompts = set()

        for seed in range(50):
            condition = generate_condition(seed=seed)
            prompt = condition_to_prompt(condition)
            prompts.add(prompt)

        # Should have good diversity (at least 20 unique prompts out of 50)
        assert len(prompts) >= 20, f"Low diversity: only {len(prompts)} unique prompts"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_generate_with_zero_seed(self):
        """Test generation with seed=0 (valid edge case)."""
        result = generate_condition(seed=0)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_generate_with_negative_seed(self):
        """Test generation with negative seed (valid in Python)."""
        result = generate_condition(seed=-1)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_generate_with_large_seed(self):
        """Test generation with very large seed."""
        result = generate_condition(seed=999999999)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_condition_to_prompt_preserves_order(self):
        """Test that condition_to_prompt preserves dict insertion order (Python 3.7+)."""
        # Create condition with known order
        condition = {}
        condition["physique"] = "wiry"
        condition["wealth"] = "poor"
        condition["age"] = "old"

        result = condition_to_prompt(condition)

        # Should be in insertion order
        assert result == "wiry, poor, old"
