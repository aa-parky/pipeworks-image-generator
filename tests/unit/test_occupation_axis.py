"""Unit tests for occupation condition generation system.

This module tests the occupation_axis module which implements
a structured, rule-based system for generating coherent occupation characteristics.

Test coverage includes:
- Weighted random selection
- Occupation generation with mandatory/optional axes
- Semantic exclusion rules
- Reproducibility via seeding
- Prompt text formatting
- Helper functions
"""

import pytest

from pipeworks.core.condition_axis import (
    OCCUPATION_AXES,
    OCCUPATION_EXCLUSIONS,
    OCCUPATION_POLICY,
    OCCUPATION_WEIGHTS,
    generate_occupation_condition,
    get_available_occupation_axes,
    get_occupation_axis_values,
    occupation_condition_to_prompt,
)

# ============================================================================
# Test Data Structures
# ============================================================================


class TestDataStructures:
    """Test that data structures are well-formed and valid."""

    def test_occupation_axes_structure(self):
        """Test OCCUPATION_AXES has expected structure."""
        assert isinstance(OCCUPATION_AXES, dict)
        assert len(OCCUPATION_AXES) > 0

        # All axes should have non-empty value lists
        for axis, values in OCCUPATION_AXES.items():
            assert isinstance(axis, str)
            assert isinstance(values, list)
            assert len(values) > 0
            # All values should be strings
            assert all(isinstance(v, str) for v in values)

    def test_occupation_axes_expected_axes(self):
        """Test that OCCUPATION_AXES contains expected axes."""
        expected_axes = ["legitimacy", "visibility", "moral_load", "dependency", "risk_exposure"]

        for axis in expected_axes:
            assert axis in OCCUPATION_AXES, f"Expected axis '{axis}' not found"

    def test_occupation_axes_expected_values(self):
        """Test that specific axes have expected values."""
        # Test legitimacy axis
        assert set(OCCUPATION_AXES["legitimacy"]) == {
            "sanctioned",
            "tolerated",
            "questioned",
            "illicit",
        }

        # Test visibility axis
        assert set(OCCUPATION_AXES["visibility"]) == {
            "hidden",
            "discreet",
            "routine",
            "conspicuous",
        }

        # Test moral_load axis
        assert set(OCCUPATION_AXES["moral_load"]) == {
            "neutral",
            "burdened",
            "conflicted",
            "corrosive",
        }

        # Test dependency axis
        assert set(OCCUPATION_AXES["dependency"]) == {
            "optional",
            "useful",
            "necessary",
            "unavoidable",
        }

        # Test risk_exposure axis
        assert set(OCCUPATION_AXES["risk_exposure"]) == {
            "benign",
            "straining",
            "hazardous",
            "eroding",
        }

    def test_occupation_policy_structure(self):
        """Test OCCUPATION_POLICY has expected structure."""
        assert isinstance(OCCUPATION_POLICY, dict)
        assert "mandatory" in OCCUPATION_POLICY
        assert "optional" in OCCUPATION_POLICY
        assert "max_optional" in OCCUPATION_POLICY

        # Mandatory and optional should be lists
        assert isinstance(OCCUPATION_POLICY["mandatory"], list)
        assert isinstance(OCCUPATION_POLICY["optional"], list)
        assert isinstance(OCCUPATION_POLICY["max_optional"], int)

        # max_optional should be reasonable
        assert OCCUPATION_POLICY["max_optional"] > 0
        assert OCCUPATION_POLICY["max_optional"] <= len(OCCUPATION_POLICY["optional"])

    def test_occupation_policy_mandatory_axes(self):
        """Test that OCCUPATION_POLICY defines expected mandatory axes."""
        # Should have legitimacy and visibility as mandatory
        assert "legitimacy" in OCCUPATION_POLICY["mandatory"]
        assert "visibility" in OCCUPATION_POLICY["mandatory"]

    def test_occupation_policy_references_valid_axes(self):
        """Test that OCCUPATION_POLICY only references defined axes."""
        all_policy_axes = OCCUPATION_POLICY["mandatory"] + OCCUPATION_POLICY["optional"]

        for axis in all_policy_axes:
            assert axis in OCCUPATION_AXES, f"Axis '{axis}' in policy but not in OCCUPATION_AXES"

    def test_no_overlap_mandatory_optional(self):
        """Test that mandatory and optional axes don't overlap."""
        mandatory_set = set(OCCUPATION_POLICY["mandatory"])
        optional_set = set(OCCUPATION_POLICY["optional"])

        overlap = mandatory_set & optional_set
        assert len(overlap) == 0, f"Axes appear in both mandatory and optional: {overlap}"

    def test_weights_structure(self):
        """Test OCCUPATION_WEIGHTS has expected structure."""
        assert isinstance(OCCUPATION_WEIGHTS, dict)

        for axis, weight_dict in OCCUPATION_WEIGHTS.items():
            assert axis in OCCUPATION_AXES, f"Weighted axis '{axis}' not in OCCUPATION_AXES"
            assert isinstance(weight_dict, dict)

            # All weighted values should exist in the axis
            for value, weight in weight_dict.items():
                assert (
                    value in OCCUPATION_AXES[axis]
                ), f"Weighted value '{value}' not in axis '{axis}'"
                assert isinstance(weight, int | float)
                assert weight > 0, f"Weight for {axis}.{value} must be positive"

    def test_exclusions_structure(self):
        """Test OCCUPATION_EXCLUSIONS has expected structure."""
        assert isinstance(OCCUPATION_EXCLUSIONS, dict)

        for (axis, value), blocked in OCCUPATION_EXCLUSIONS.items():
            # Trigger axis/value should exist
            assert axis in OCCUPATION_AXES, f"Exclusion trigger axis '{axis}' not defined"
            assert (
                value in OCCUPATION_AXES[axis]
            ), f"Exclusion trigger value '{value}' not in axis '{axis}'"

            # Blocked axes/values should exist
            assert isinstance(blocked, dict)
            for blocked_axis, blocked_values in blocked.items():
                assert blocked_axis in OCCUPATION_AXES, f"Blocked axis '{blocked_axis}' not defined"
                for blocked_value in blocked_values:
                    assert (
                        blocked_value in OCCUPATION_AXES[blocked_axis]
                    ), f"Blocked value '{blocked_value}' not in axis '{blocked_axis}'"

    def test_exclusions_semantic_rules(self):
        """Test that key semantic exclusion rules are defined."""
        # Illicit should exclude conspicuous
        assert ("legitimacy", "illicit") in OCCUPATION_EXCLUSIONS
        illicit_blocked = OCCUPATION_EXCLUSIONS[("legitimacy", "illicit")]
        assert "visibility" in illicit_blocked
        assert "conspicuous" in illicit_blocked["visibility"]

        # Sanctioned should exclude hidden
        assert ("legitimacy", "sanctioned") in OCCUPATION_EXCLUSIONS
        sanctioned_blocked = OCCUPATION_EXCLUSIONS[("legitimacy", "sanctioned")]
        assert "visibility" in sanctioned_blocked
        assert "hidden" in sanctioned_blocked["visibility"]


# ============================================================================
# Test generate_occupation_condition Function
# ============================================================================


class TestGenerateOccupationCondition:
    """Test main occupation generation function."""

    def test_generate_occupation_condition_returns_dict(self):
        """Test that generate_occupation_condition returns a dictionary."""
        result = generate_occupation_condition(seed=42)
        assert isinstance(result, dict)

    def test_generate_occupation_condition_includes_mandatory_axes(self):
        """Test that all mandatory axes are included."""
        result = generate_occupation_condition(seed=42)

        for axis in OCCUPATION_POLICY["mandatory"]:
            assert axis in result, f"Mandatory axis '{axis}' not in result"
            assert result[axis] in OCCUPATION_AXES[axis]

    def test_generate_occupation_condition_respects_max_optional(self):
        """Test that number of optional axes respects max_optional limit."""
        # Run multiple times to test different random outcomes
        for seed in range(20):
            result = generate_occupation_condition(seed=seed)

            optional_count = sum(1 for axis in OCCUPATION_POLICY["optional"] if axis in result)

            max_optional = OCCUPATION_POLICY["max_optional"]
            assert (
                optional_count <= max_optional
            ), f"Too many optional axes: {optional_count} > {max_optional}"

    def test_generate_occupation_condition_all_values_valid(self):
        """Test that all selected values are valid for their axes."""
        for seed in range(10):
            result = generate_occupation_condition(seed=seed)

            for axis, value in result.items():
                assert axis in OCCUPATION_AXES, f"Invalid axis '{axis}' in result"
                assert value in OCCUPATION_AXES[axis], f"Invalid value '{value}' for axis '{axis}'"

    def test_generate_occupation_condition_reproducible_with_seed(self):
        """Test that same seed produces same occupation condition."""
        result1 = generate_occupation_condition(seed=42)
        result2 = generate_occupation_condition(seed=42)

        assert result1 == result2

    def test_generate_occupation_condition_different_without_seed(self):
        """Test that conditions vary without seed (statistical test)."""
        # Generate many conditions and check for variation
        results = [generate_occupation_condition() for _ in range(20)]

        # Convert to tuples for set comparison
        result_tuples = [tuple(sorted(r.items())) for r in results]

        # Should have at least some variation (not all identical)
        unique_results = len(set(result_tuples))
        assert unique_results > 1, "All conditions were identical (very unlikely without seed)"

    def test_generate_occupation_condition_applies_exclusions(self):
        """Test that exclusion rules are applied correctly."""
        # This is a statistical test - run many generations and check exclusions
        violations = []

        for seed in range(100):
            result = generate_occupation_condition(seed=seed)

            # Check each exclusion rule
            for (axis, value), blocked in OCCUPATION_EXCLUSIONS.items():
                if result.get(axis) == value:
                    # This exclusion is triggered
                    for blocked_axis, blocked_values in blocked.items():
                        if result.get(blocked_axis) in blocked_values:
                            violations.append(
                                f"Seed {seed}: {axis}={value} conflicts with "
                                f"{blocked_axis}={result[blocked_axis]}"
                            )

        assert len(violations) == 0, f"Exclusion violations: {violations}"

    def test_generate_occupation_condition_handles_none_seed(self):
        """Test that generate_occupation_condition works with seed=None (non-reproducible)."""
        result = generate_occupation_condition(seed=None)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_generate_occupation_condition_weighted_distribution(self):
        """Test that weights affect probability distribution (statistical test)."""
        # Focus on legitimacy axis which has strong weights
        legitimacy_counts = {}

        for seed in range(500):
            result = generate_occupation_condition(seed=seed)
            if "legitimacy" in result:
                legitimacy = result["legitimacy"]
                legitimacy_counts[legitimacy] = legitimacy_counts.get(legitimacy, 0) + 1

        # "sanctioned" should be most common (weight=4), "illicit" should be rarest (weight=0.5)
        if legitimacy_counts:
            # Statistical assertion: sanctioned should appear more than illicit
            if "sanctioned" in legitimacy_counts and "illicit" in legitimacy_counts:
                assert legitimacy_counts["sanctioned"] > legitimacy_counts["illicit"]

    def test_generate_occupation_condition_no_illicit_conspicuous(self):
        """Test that illicit occupations are never conspicuous (exclusion rule)."""
        # Run many generations
        for seed in range(100):
            result = generate_occupation_condition(seed=seed)

            # If legitimacy is illicit, visibility should not be conspicuous
            if result.get("legitimacy") == "illicit":
                assert result.get("visibility") != "conspicuous", (
                    f"Seed {seed}: illicit occupation should not be conspicuous "
                    f"(got visibility={result.get('visibility')})"
                )

    def test_generate_occupation_condition_no_sanctioned_hidden(self):
        """Test that sanctioned occupations are never hidden (exclusion rule)."""
        # Run many generations
        for seed in range(100):
            result = generate_occupation_condition(seed=seed)

            # If legitimacy is sanctioned, visibility should not be hidden
            if result.get("legitimacy") == "sanctioned":
                assert result.get("visibility") != "hidden", (
                    f"Seed {seed}: sanctioned occupation should not be hidden "
                    f"(got visibility={result.get('visibility')})"
                )


# ============================================================================
# Test occupation_condition_to_prompt Function
# ============================================================================


class TestOccupationConditionToPrompt:
    """Test prompt text generation function."""

    def test_occupation_condition_to_prompt_basic(self):
        """Test basic prompt text generation."""
        condition = {"legitimacy": "tolerated", "visibility": "discreet"}
        result = occupation_condition_to_prompt(condition)

        assert isinstance(result, str)
        assert "tolerated" in result
        assert "discreet" in result
        assert ", " in result  # Comma-separated

    def test_occupation_condition_to_prompt_empty(self):
        """Test prompt generation with empty condition."""
        result = occupation_condition_to_prompt({})
        assert result == ""

    def test_occupation_condition_to_prompt_single_axis(self):
        """Test prompt generation with single axis."""
        condition = {"legitimacy": "sanctioned"}
        result = occupation_condition_to_prompt(condition)

        assert result == "sanctioned"

    def test_occupation_condition_to_prompt_multiple_axes(self):
        """Test prompt generation with multiple axes."""
        condition = {
            "legitimacy": "tolerated",
            "visibility": "discreet",
            "moral_load": "burdened",
        }
        result = occupation_condition_to_prompt(condition)

        # Should be comma-separated
        parts = result.split(", ")
        assert len(parts) == 3
        assert "tolerated" in parts
        assert "discreet" in parts
        assert "burdened" in parts

    def test_occupation_condition_to_prompt_integration(self):
        """Test prompt generation from generated condition."""
        condition = generate_occupation_condition(seed=42)
        result = occupation_condition_to_prompt(condition)

        assert isinstance(result, str)
        assert len(result) > 0
        # Should have commas (multiple axes) unless only one axis
        assert ", " in result or len(condition) == 1

    def test_occupation_condition_to_prompt_all_axes(self):
        """Test prompt generation with all possible axes."""
        condition = {
            "legitimacy": "questioned",
            "visibility": "routine",
            "moral_load": "conflicted",
            "dependency": "necessary",
            "risk_exposure": "hazardous",
        }
        result = occupation_condition_to_prompt(condition)

        # All values should be in the result
        for value in condition.values():
            assert value in result


# ============================================================================
# Test Helper Functions
# ============================================================================


class TestHelperFunctions:
    """Test utility and helper functions."""

    def test_get_available_occupation_axes(self):
        """Test get_available_occupation_axes returns all axes."""
        axes = get_available_occupation_axes()

        assert isinstance(axes, list)
        assert len(axes) == len(OCCUPATION_AXES)

        # All axes should be present
        for axis in OCCUPATION_AXES:
            assert axis in axes

    def test_get_occupation_axis_values(self):
        """Test get_occupation_axis_values returns correct values."""
        for axis in OCCUPATION_AXES:
            values = get_occupation_axis_values(axis)

            assert isinstance(values, list)
            assert values == OCCUPATION_AXES[axis]

    def test_get_occupation_axis_values_invalid_axis(self):
        """Test get_occupation_axis_values raises error for invalid axis."""
        with pytest.raises(KeyError):
            get_occupation_axis_values("nonexistent_axis")

    def test_get_occupation_axis_values_specific_axes(self):
        """Test get_occupation_axis_values for specific axes."""
        # Test legitimacy
        legitimacy_values = get_occupation_axis_values("legitimacy")
        assert set(legitimacy_values) == {"sanctioned", "tolerated", "questioned", "illicit"}

        # Test visibility
        visibility_values = get_occupation_axis_values("visibility")
        assert set(visibility_values) == {"hidden", "discreet", "routine", "conspicuous"}


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Test full workflow integration."""

    def test_full_generation_workflow(self):
        """Test complete workflow: generate -> convert -> use."""
        # Step 1: Generate occupation condition
        condition = generate_occupation_condition(seed=42)
        assert isinstance(condition, dict)
        assert len(condition) > 0

        # Step 2: Convert to prompt
        prompt = occupation_condition_to_prompt(condition)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

        # Step 3: Verify all condition values are in prompt
        for value in condition.values():
            assert value in prompt

    def test_reproducible_workflow(self):
        """Test that entire workflow is reproducible with seed."""
        # Run 1
        condition1 = generate_occupation_condition(seed=12345)
        prompt1 = occupation_condition_to_prompt(condition1)

        # Run 2
        condition2 = generate_occupation_condition(seed=12345)
        prompt2 = occupation_condition_to_prompt(condition2)

        assert condition1 == condition2
        assert prompt1 == prompt2

    def test_multiple_generations_diversity(self):
        """Test that multiple generations produce diverse results."""
        prompts = set()

        for seed in range(50):
            condition = generate_occupation_condition(seed=seed)
            prompt = occupation_condition_to_prompt(condition)
            prompts.add(prompt)

        # Should have good diversity (at least 20 unique prompts out of 50)
        assert len(prompts) >= 20, f"Low diversity: only {len(prompts)} unique prompts"

    def test_combined_with_character_conditions(self):
        """Test that occupation conditions can be combined with character conditions."""
        from pipeworks.core.condition_axis import condition_to_prompt, generate_condition

        # Generate both types
        char = generate_condition(seed=42)
        occupation = generate_occupation_condition(seed=42)

        # Convert both to prompts
        char_prompt = condition_to_prompt(char)
        occupation_prompt = occupation_condition_to_prompt(occupation)

        # Combine
        combined = f"{char_prompt}, {occupation_prompt}"

        assert isinstance(combined, str)
        assert len(combined) > 0
        # Should contain elements from both
        assert any(value in combined for value in char.values())
        assert any(value in combined for value in occupation.values())


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_generate_with_zero_seed(self):
        """Test generation with seed=0 (valid edge case)."""
        result = generate_occupation_condition(seed=0)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_generate_with_negative_seed(self):
        """Test generation with negative seed (valid in Python)."""
        result = generate_occupation_condition(seed=-1)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_generate_with_large_seed(self):
        """Test generation with very large seed."""
        result = generate_occupation_condition(seed=999999999)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_occupation_condition_to_prompt_preserves_order(self):
        """Test that occupation_condition_to_prompt preserves dict insertion order (Python 3.7+)."""
        # Create condition with known order
        condition = {}
        condition["legitimacy"] = "tolerated"
        condition["visibility"] = "discreet"
        condition["moral_load"] = "burdened"

        result = occupation_condition_to_prompt(condition)

        # Should be in insertion order
        assert result == "tolerated, discreet, burdened"

    def test_minimum_mandatory_axes_usually_present(self):
        """Test that mandatory axes are usually present (unless removed by exclusions).

        Note: In rare cases, exclusions between mandatory axes (legitimacy + visibility)
        may remove one of them. For example, if legitimacy='illicit' is selected and
        then visibility='conspicuous' is selected, the exclusion will remove visibility.
        This is acceptable behavior - exclusions take precedence over policy.
        """
        legitimacy_count = 0
        visibility_count = 0
        both_count = 0

        for seed in range(50):
            result = generate_occupation_condition(seed=seed)

            has_legitimacy = "legitimacy" in result
            has_visibility = "visibility" in result

            if has_legitimacy:
                legitimacy_count += 1
            if has_visibility:
                visibility_count += 1
            if has_legitimacy and has_visibility:
                both_count += 1

            # At least one mandatory axis should always be present
            assert (
                has_legitimacy or has_visibility
            ), f"Seed {seed}: No mandatory axes present (result: {result})"

        # Statistical checks: most generations should have both mandatory axes
        # (exclusions should be rare since weights make conflicts unlikely)
        assert legitimacy_count >= 45, f"Only {legitimacy_count}/50 had legitimacy"
        assert visibility_count >= 45, f"Only {visibility_count}/50 had visibility"
        assert both_count >= 40, f"Only {both_count}/50 had both mandatory axes"

    def test_maximum_axes_never_exceeded(self):
        """Test that total axes never exceeds mandatory + max_optional."""
        max_total = len(OCCUPATION_POLICY["mandatory"]) + OCCUPATION_POLICY["max_optional"]

        for seed in range(50):
            result = generate_occupation_condition(seed=seed)
            assert len(result) <= max_total, f"Too many axes: {len(result)} > {max_total}"


# ============================================================================
# Semantic Validation Tests
# ============================================================================


class TestSemanticValidation:
    """Test that generated conditions make semantic sense."""

    def test_no_hidden_unavoidable(self):
        """Test that hidden occupations are never unavoidable (exclusion rule)."""
        for seed in range(100):
            result = generate_occupation_condition(seed=seed)

            # If visibility is hidden, dependency should not be unavoidable
            if result.get("visibility") == "hidden":
                assert result.get("dependency") != "unavoidable", (
                    f"Seed {seed}: hidden occupation should not be unavoidable "
                    f"(got dependency={result.get('dependency')})"
                )

    def test_no_eroding_neutral(self):
        """Test that eroding risk exposure never has neutral moral load (exclusion rule)."""
        for seed in range(100):
            result = generate_occupation_condition(seed=seed)

            # If risk_exposure is eroding, moral_load should not be neutral
            if result.get("risk_exposure") == "eroding":
                assert result.get("moral_load") != "neutral", (
                    f"Seed {seed}: eroding risk should not have neutral moral load "
                    f"(got moral_load={result.get('moral_load')})"
                )

    def test_no_optional_eroding(self):
        """Test that optional work is never eroding (exclusion rule)."""
        for seed in range(100):
            result = generate_occupation_condition(seed=seed)

            # If dependency is optional, risk_exposure should not be eroding
            if result.get("dependency") == "optional":
                assert result.get("risk_exposure") != "eroding", (
                    f"Seed {seed}: optional work should not be eroding "
                    f"(got risk_exposure={result.get('risk_exposure')})"
                )
