"""Unit tests for condition generation handlers.

This module tests the UI handlers for generating character and facial conditions
in Start 2 and Start 3 segments.

Test coverage includes:
- Character condition generation
- Facial condition generation
- Combined (Both) condition generation
- Condition type validation
"""

import pytest

from pipeworks.ui.handlers.conditions import generate_condition_by_type


class TestGenerateConditionByType:
    """Test the main condition generation handler."""

    def test_generate_none_returns_empty(self):
        """Test that 'None' condition type returns empty string."""
        result = generate_condition_by_type("None")
        assert result == ""

    def test_generate_character_conditions(self):
        """Test character condition generation."""
        result = generate_condition_by_type("Character", seed=42)
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain character condition keywords
        # (actual values depend on seed, so we just check it's not empty)

    def test_generate_facial_conditions(self):
        """Test facial condition generation."""
        result = generate_condition_by_type("Facial", seed=42)
        # Facial conditions are always generated (facial_signal is mandatory)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_both_conditions(self):
        """Test combined condition generation."""
        result = generate_condition_by_type("Both", seed=42)
        assert isinstance(result, str)
        # "Both" should always have at least character conditions
        # (since character conditions are always generated, facial may be empty)
        assert len(result) > 0

    def test_character_reproducible_with_seed(self):
        """Test that character conditions are reproducible with seed."""
        result1 = generate_condition_by_type("Character", seed=12345)
        result2 = generate_condition_by_type("Character", seed=12345)
        assert result1 == result2

    def test_facial_reproducible_with_seed(self):
        """Test that facial conditions are reproducible with seed."""
        result1 = generate_condition_by_type("Facial", seed=12345)
        result2 = generate_condition_by_type("Facial", seed=12345)
        assert result1 == result2

    def test_both_reproducible_with_seed(self):
        """Test that combined conditions are reproducible with seed."""
        result1 = generate_condition_by_type("Both", seed=12345)
        result2 = generate_condition_by_type("Both", seed=12345)
        assert result1 == result2

    def test_character_different_without_seed(self):
        """Test that character conditions vary without seed."""
        results = [generate_condition_by_type("Character") for _ in range(10)]
        # Should have some variation
        unique_results = set(results)
        assert len(unique_results) > 1, "All conditions were identical"

    def test_both_contains_character_and_maybe_facial(self):
        """Test that 'Both' includes character conditions and maybe facial."""
        # Try multiple seeds to get a case with both
        for seed in range(20):
            result = generate_condition_by_type("Both", seed=seed)
            # Should always have character conditions at minimum
            assert len(result) > 0

            # Check if it's truly combined (has a comma indicating multiple parts)
            # Note: This might fail if facial is empty, which is valid
            # So we just check that the result is valid

    def test_unknown_condition_type_returns_empty(self):
        """Test that unknown condition types return empty string."""
        result = generate_condition_by_type("InvalidType")
        assert result == ""

    def test_facial_never_empty(self):
        """Test that facial conditions are never empty (facial_signal is mandatory)."""
        # Try multiple seeds, should never get empty results
        results = [generate_condition_by_type("Facial", seed=seed) for seed in range(100)]
        empty_count = sum(1 for r in results if r == "")
        # facial_signal is mandatory - should always generate
        assert empty_count == 0, f"Expected 0 empty, got {empty_count} (facial_signal is mandatory)"

    def test_character_never_empty(self):
        """Test that character conditions are never empty."""
        # Try multiple seeds
        for seed in range(50):
            result = generate_condition_by_type("Character", seed=seed)
            assert len(result) > 0, f"Character condition was empty for seed {seed}"


class TestConditionFormat:
    """Test that generated conditions have correct format."""

    def test_character_format(self):
        """Test that character conditions are comma-separated."""
        result = generate_condition_by_type("Character", seed=42)
        # Should contain commas (multiple attributes)
        assert ", " in result

    def test_facial_format_when_not_empty(self):
        """Test that facial conditions are single words or empty."""
        # Find a seed that produces a non-empty facial condition
        for seed in range(100):
            result = generate_condition_by_type("Facial", seed=seed)
            if result:
                # Facial conditions are single words (no commas)
                assert ", " not in result
                break

    def test_both_format(self):
        """Test that 'Both' conditions are properly combined."""
        # Find a seed that has both character and facial
        for seed in range(100):
            result = generate_condition_by_type("Both", seed=seed)
            if result and result.count(", ") > 1:
                # Has multiple parts, likely includes both character and facial
                # Just verify it's a valid comma-separated string
                parts = result.split(", ")
                assert all(part.strip() for part in parts), "Empty parts in condition"
                break


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_string_condition_type(self):
        """Test handling of empty string condition type."""
        result = generate_condition_by_type("")
        assert result == ""

    def test_none_value_condition_type(self):
        """Test that lowercase 'none' is not treated same as 'None'."""
        result = generate_condition_by_type("none")
        # Lowercase should return empty (unknown type)
        assert result == ""

    def test_case_sensitive_condition_types(self):
        """Test that condition types are case-sensitive."""
        # These should all return empty (invalid types)
        assert generate_condition_by_type("character") == ""
        assert generate_condition_by_type("FACIAL") == ""
        assert generate_condition_by_type("both") == ""

    def test_whitespace_condition_type(self):
        """Test handling of whitespace in condition type."""
        result = generate_condition_by_type(" None ")
        # Should return empty (not exact match)
        assert result == ""
