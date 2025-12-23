"""Unit tests for facial condition generation system.

This module tests the facial_conditions module which implements a structured
system for generating facial signal descriptors that modulate character perception.

NOTE: This test suite mirrors test_character_conditions.py intentionally, as the
facial_conditions module is designed for eventual merger into character_conditions.py.

Test coverage includes:
- Weighted random selection
- Condition generation with optional-only axes
- Semantic exclusion rules (currently minimal)
- Reproducibility via seeding
- Prompt text formatting
- Helper functions
- Empty result handling (no facial signal selected)
"""

import random

import pytest

from pipeworks.core.facial_conditions import (
    FACIAL_AXES,
    FACIAL_EXCLUSIONS,
    FACIAL_POLICY,
    FACIAL_WEIGHTS,
    facial_condition_to_prompt,
    generate_facial_condition,
    get_available_facial_axes,
    get_facial_axis_values,
    weighted_choice,
)

# ============================================================================
# Test Data Structures
# ============================================================================


class TestDataStructures:
    """Test that data structures are well-formed and valid."""

    def test_facial_axes_structure(self):
        """Test FACIAL_AXES has expected structure."""
        assert isinstance(FACIAL_AXES, dict)
        assert len(FACIAL_AXES) > 0

        # All axes should have non-empty value lists
        for axis, values in FACIAL_AXES.items():
            assert isinstance(axis, str)
            assert isinstance(values, list)
            assert len(values) > 0
            # All values should be strings
            assert all(isinstance(v, str) for v in values)

    def test_facial_axes_contains_expected_signals(self):
        """Test that facial_signal axis contains all expected values."""
        assert "facial_signal" in FACIAL_AXES
        expected_signals = [
            "understated",
            "pronounced",
            "exaggerated",
            "asymmetrical",
            "weathered",
            "soft-featured",
            "sharp-featured",
        ]
        assert set(FACIAL_AXES["facial_signal"]) == set(expected_signals)

    def test_facial_policy_structure(self):
        """Test FACIAL_POLICY has expected structure."""
        assert isinstance(FACIAL_POLICY, dict)
        assert "mandatory" in FACIAL_POLICY
        assert "optional" in FACIAL_POLICY
        assert "max_optional" in FACIAL_POLICY

        # Mandatory and optional should be lists
        assert isinstance(FACIAL_POLICY["mandatory"], list)
        assert isinstance(FACIAL_POLICY["optional"], list)
        assert isinstance(FACIAL_POLICY["max_optional"], int)

        # max_optional should be reasonable
        assert FACIAL_POLICY["max_optional"] >= 0
        assert FACIAL_POLICY["max_optional"] <= len(FACIAL_POLICY["optional"])

    def test_facial_policy_no_mandatory_axes(self):
        """Test that facial signals have no mandatory axes (all optional)."""
        assert len(FACIAL_POLICY["mandatory"]) == 0, "Facial signals should all be optional"

    def test_facial_policy_references_valid_axes(self):
        """Test that FACIAL_POLICY only references defined axes."""
        all_policy_axes = FACIAL_POLICY["mandatory"] + FACIAL_POLICY["optional"]

        for axis in all_policy_axes:
            assert axis in FACIAL_AXES, f"Axis '{axis}' in policy but not in FACIAL_AXES"

    def test_no_overlap_mandatory_optional(self):
        """Test that mandatory and optional axes don't overlap."""
        mandatory_set = set(FACIAL_POLICY["mandatory"])
        optional_set = set(FACIAL_POLICY["optional"])

        overlap = mandatory_set & optional_set
        assert len(overlap) == 0, f"Axes appear in both mandatory and optional: {overlap}"

    def test_facial_weights_structure(self):
        """Test FACIAL_WEIGHTS has expected structure."""
        assert isinstance(FACIAL_WEIGHTS, dict)

        for axis, weight_dict in FACIAL_WEIGHTS.items():
            assert axis in FACIAL_AXES, f"Weighted axis '{axis}' not in FACIAL_AXES"
            assert isinstance(weight_dict, dict)

            # All weighted values should exist in the axis
            for value, weight in weight_dict.items():
                assert value in FACIAL_AXES[axis], f"Weighted value '{value}' not in axis '{axis}'"
                assert isinstance(weight, (int, float))
                assert weight > 0, f"Weight for {axis}.{value} must be positive"

    def test_facial_weights_complete_coverage(self):
        """Test that all facial_signal values have weights defined."""
        assert "facial_signal" in FACIAL_WEIGHTS
        facial_signal_values = set(FACIAL_AXES["facial_signal"])
        weighted_values = set(FACIAL_WEIGHTS["facial_signal"].keys())
        assert facial_signal_values == weighted_values, "All facial signals should have weights"

    def test_facial_exclusions_structure(self):
        """Test FACIAL_EXCLUSIONS has expected structure."""
        assert isinstance(FACIAL_EXCLUSIONS, dict)

        for (axis, value), blocked in FACIAL_EXCLUSIONS.items():
            # Trigger axis/value should exist
            assert axis in FACIAL_AXES, f"Exclusion trigger axis '{axis}' not defined"
            assert (
                value in FACIAL_AXES[axis]
            ), f"Exclusion trigger value '{value}' not in axis '{axis}'"

            # Blocked axes/values should exist
            assert isinstance(blocked, dict)
            for blocked_axis, blocked_values in blocked.items():
                assert blocked_axis in FACIAL_AXES, f"Blocked axis '{blocked_axis}' not defined"
                for blocked_value in blocked_values:
                    assert (
                        blocked_value in FACIAL_AXES[blocked_axis]
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
# Test generate_facial_condition Function
# ============================================================================


class TestGenerateFacialCondition:
    """Test main facial condition generation function."""

    def test_generate_facial_condition_returns_dict(self):
        """Test that generate_facial_condition returns a dictionary."""
        result = generate_facial_condition(seed=42)
        assert isinstance(result, dict)

    def test_generate_facial_condition_can_be_empty(self):
        """Test that facial condition can be empty (no signal selected)."""
        # Run multiple times to test different random outcomes
        results = [generate_facial_condition(seed=seed) for seed in range(50)]

        # At least some should be empty (50% chance with max_optional=1)
        empty_count = sum(1 for r in results if len(r) == 0)
        assert empty_count > 0, "Should have at least some empty results"

        # At least some should be non-empty
        non_empty_count = sum(1 for r in results if len(r) > 0)
        assert non_empty_count > 0, "Should have at least some non-empty results"

    def test_generate_facial_condition_includes_mandatory_axes(self):
        """Test that all mandatory axes are included (currently none)."""
        result = generate_facial_condition(seed=42)

        for axis in FACIAL_POLICY["mandatory"]:
            assert axis in result, f"Mandatory axis '{axis}' not in result"
            assert result[axis] in FACIAL_AXES[axis]

    def test_generate_facial_condition_respects_max_optional(self):
        """Test that number of optional axes respects max_optional limit."""
        # Run multiple times to test different random outcomes
        for seed in range(50):
            result = generate_facial_condition(seed=seed)

            optional_count = sum(1 for axis in FACIAL_POLICY["optional"] if axis in result)

            max_optional = FACIAL_POLICY["max_optional"]
            assert (
                optional_count <= max_optional
            ), f"Too many optional axes: {optional_count} > {max_optional}"

    def test_generate_facial_condition_max_one_signal(self):
        """Test that at most one facial signal is selected."""
        for seed in range(100):
            result = generate_facial_condition(seed=seed)

            # Should have 0 or 1 facial_signal
            assert len(result) <= 1, f"Expected at most 1 facial signal, got {len(result)}"

    def test_generate_facial_condition_all_values_valid(self):
        """Test that all selected values are valid for their axes."""
        for seed in range(50):
            result = generate_facial_condition(seed=seed)

            for axis, value in result.items():
                assert axis in FACIAL_AXES, f"Invalid axis '{axis}' in result"
                assert value in FACIAL_AXES[axis], f"Invalid value '{value}' for axis '{axis}'"

    def test_generate_facial_condition_reproducible_with_seed(self):
        """Test that same seed produces same condition."""
        result1 = generate_facial_condition(seed=42)
        result2 = generate_facial_condition(seed=42)

        assert result1 == result2

    def test_generate_facial_condition_different_seeds_vary(self):
        """Test that different seeds can produce different results."""
        # Generate many conditions and check for variation
        results = [generate_facial_condition(seed=seed) for seed in range(50)]

        # Convert to tuples for set comparison
        result_tuples = [tuple(sorted(r.items())) for r in results]

        # Should have variation (not all identical)
        unique_results = len(set(result_tuples))
        assert unique_results > 1, "All conditions were identical (very unlikely)"

    def test_generate_facial_condition_applies_exclusions(self):
        """Test that exclusion rules are applied correctly."""
        # This is a statistical test - run many generations and check exclusions
        violations = []

        for seed in range(100):
            result = generate_facial_condition(seed=seed)

            # Check each exclusion rule
            for (axis, value), blocked in FACIAL_EXCLUSIONS.items():
                if result.get(axis) == value:
                    # This exclusion is triggered
                    for blocked_axis, blocked_values in blocked.items():
                        if result.get(blocked_axis) in blocked_values:
                            violations.append(
                                f"Seed {seed}: {axis}={value} conflicts with "
                                f"{blocked_axis}={result[blocked_axis]}"
                            )

        assert len(violations) == 0, f"Exclusion violations: {violations}"

    def test_generate_facial_condition_handles_none_seed(self):
        """Test that generate_facial_condition works with seed=None (non-reproducible)."""
        result = generate_facial_condition(seed=None)
        assert isinstance(result, dict)
        # Result can be empty (no facial signal selected)

    def test_generate_facial_condition_weighted_distribution(self):
        """Test that weights affect probability distribution (statistical test)."""
        # Focus on facial_signal axis which has defined weights
        signal_counts = {}

        for seed in range(500):
            result = generate_facial_condition(seed=seed)
            if "facial_signal" in result:
                signal = result["facial_signal"]
                signal_counts[signal] = signal_counts.get(signal, 0) + 1

        # Should have collected some signals
        assert len(signal_counts) > 0, "No facial signals were generated"

        # "understated" should be most common (weight=3.0)
        # "exaggerated" should be rarest (weight=0.5)
        if "understated" in signal_counts and "exaggerated" in signal_counts:
            assert (
                signal_counts["understated"] > signal_counts["exaggerated"]
            ), "Weighted distribution not working correctly"


# ============================================================================
# Test facial_condition_to_prompt Function
# ============================================================================


class TestFacialConditionToPrompt:
    """Test prompt text generation function."""

    def test_facial_condition_to_prompt_basic(self):
        """Test basic prompt text generation."""
        condition = {"facial_signal": "weathered"}
        result = facial_condition_to_prompt(condition)

        assert isinstance(result, str)
        assert "weathered" in result

    def test_facial_condition_to_prompt_empty(self):
        """Test prompt generation with empty condition (no facial signal)."""
        result = facial_condition_to_prompt({})
        assert result == ""

    def test_facial_condition_to_prompt_single_signal(self):
        """Test prompt generation with single facial signal."""
        condition = {"facial_signal": "soft-featured"}
        result = facial_condition_to_prompt(condition)

        assert result == "soft-featured"

    def test_facial_condition_to_prompt_all_signals(self):
        """Test prompt generation for each possible facial signal."""
        for signal in FACIAL_AXES["facial_signal"]:
            condition = {"facial_signal": signal}
            result = facial_condition_to_prompt(condition)

            assert result == signal
            assert isinstance(result, str)

    def test_facial_condition_to_prompt_integration(self):
        """Test prompt generation from generated condition."""
        for seed in range(20):
            condition = generate_facial_condition(seed=seed)
            result = facial_condition_to_prompt(condition)

            assert isinstance(result, str)

            if condition:
                # Non-empty condition should produce non-empty prompt
                assert len(result) > 0
                # Should contain the signal value
                assert condition["facial_signal"] in result
            else:
                # Empty condition should produce empty prompt
                assert result == ""


# ============================================================================
# Test Helper Functions
# ============================================================================


class TestHelperFunctions:
    """Test utility and helper functions."""

    def test_get_available_facial_axes(self):
        """Test get_available_facial_axes returns all axes."""
        axes = get_available_facial_axes()

        assert isinstance(axes, list)
        assert len(axes) == len(FACIAL_AXES)

        # All axes should be present
        for axis in FACIAL_AXES:
            assert axis in axes

    def test_get_available_facial_axes_contains_facial_signal(self):
        """Test that facial_signal axis is in available axes."""
        axes = get_available_facial_axes()
        assert "facial_signal" in axes

    def test_get_facial_axis_values(self):
        """Test get_facial_axis_values returns correct values."""
        for axis in FACIAL_AXES:
            values = get_facial_axis_values(axis)

            assert isinstance(values, list)
            assert values == FACIAL_AXES[axis]

    def test_get_facial_axis_values_facial_signal(self):
        """Test getting values for facial_signal axis specifically."""
        values = get_facial_axis_values("facial_signal")

        assert isinstance(values, list)
        assert len(values) == 7  # Should have all 7 facial signals
        assert "understated" in values
        assert "weathered" in values
        assert "sharp-featured" in values

    def test_get_facial_axis_values_invalid_axis(self):
        """Test get_facial_axis_values raises error for invalid axis."""
        with pytest.raises(KeyError):
            get_facial_axis_values("nonexistent_axis")


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Test full workflow integration."""

    def test_full_generation_workflow_with_signal(self):
        """Test complete workflow when a facial signal is selected."""
        # Find a seed that produces a non-empty condition
        condition = None
        for seed in range(100):
            condition = generate_facial_condition(seed=seed)
            if condition:
                break

        assert condition is not None, "Should find at least one non-empty condition"
        assert len(condition) > 0

        # Step 2: Convert to prompt
        prompt = facial_condition_to_prompt(condition)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

        # Step 3: Verify condition value is in prompt
        for value in condition.values():
            assert value in prompt

    def test_full_generation_workflow_without_signal(self):
        """Test complete workflow when no facial signal is selected."""
        # Find a seed that produces an empty condition
        condition = None
        for seed in range(100):
            condition = generate_facial_condition(seed=seed)
            if not condition:
                break

        assert condition is not None, "Should find at least one empty condition"
        assert len(condition) == 0

        # Step 2: Convert to prompt
        prompt = facial_condition_to_prompt(condition)
        assert isinstance(prompt, str)
        assert len(prompt) == 0

    def test_reproducible_workflow(self):
        """Test that entire workflow is reproducible with seed."""
        # Run 1
        condition1 = generate_facial_condition(seed=12345)
        prompt1 = facial_condition_to_prompt(condition1)

        # Run 2
        condition2 = generate_facial_condition(seed=12345)
        prompt2 = facial_condition_to_prompt(condition2)

        assert condition1 == condition2
        assert prompt1 == prompt2

    def test_multiple_generations_diversity(self):
        """Test that multiple generations produce diverse results."""
        prompts = []

        for seed in range(100):
            condition = generate_facial_condition(seed=seed)
            prompt = facial_condition_to_prompt(condition)
            prompts.append(prompt)

        # Should have good diversity (multiple different signals + empty)
        unique_prompts = set(prompts)
        assert len(unique_prompts) >= 5, f"Low diversity: only {len(unique_prompts)} unique prompts"

        # Should include empty string (no signal)
        assert "" in unique_prompts, "Should have at least one empty result"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_generate_with_zero_seed(self):
        """Test generation with seed=0 (valid edge case)."""
        result = generate_facial_condition(seed=0)
        assert isinstance(result, dict)

    def test_generate_with_negative_seed(self):
        """Test generation with negative seed (valid in Python)."""
        result = generate_facial_condition(seed=-1)
        assert isinstance(result, dict)

    def test_generate_with_large_seed(self):
        """Test generation with very large seed."""
        result = generate_facial_condition(seed=999999999)
        assert isinstance(result, dict)

    def test_facial_condition_to_prompt_preserves_order(self):
        """Test that facial_condition_to_prompt preserves dict insertion order."""
        # With max_optional=1, we only ever have one key, but test the principle
        condition = {}
        condition["facial_signal"] = "weathered"

        result = facial_condition_to_prompt(condition)
        assert result == "weathered"

    def test_multiple_empty_generations(self):
        """Test that multiple empty generations are handled correctly."""
        # Generate multiple empty conditions
        for seed in range(100):
            condition = generate_facial_condition(seed=seed)
            if not condition:
                # Empty condition should produce empty prompt
                prompt = facial_condition_to_prompt(condition)
                assert prompt == ""


# ============================================================================
# Statistical Tests
# ============================================================================


class TestStatisticalProperties:
    """Test statistical properties of generation over many samples."""

    def test_empty_result_probability(self):
        """Test that empty results occur with reasonable probability."""
        # With max_optional=1 and random.randint(0, 1), expect ~50% empty
        results = [generate_facial_condition(seed=seed) for seed in range(200)]

        empty_count = sum(1 for r in results if len(r) == 0)
        empty_ratio = empty_count / len(results)

        # Should be roughly 50% empty (allow 40-60% range for statistical variance)
        assert 0.35 <= empty_ratio <= 0.65, f"Empty ratio {empty_ratio:.2f} outside expected range"

    def test_all_signals_can_appear(self):
        """Test that all facial signals can appear over many generations."""
        signal_appearances = set()

        for seed in range(500):
            condition = generate_facial_condition(seed=seed)
            if "facial_signal" in condition:
                signal_appearances.add(condition["facial_signal"])

        # All signals should appear at least once
        expected_signals = set(FACIAL_AXES["facial_signal"])
        assert (
            signal_appearances == expected_signals
        ), f"Missing signals: {expected_signals - signal_appearances}"
