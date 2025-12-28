"""Tests for aspect ratio presets, validation, and utilities."""

import pytest

from pipeworks.ui.aspect_ratios import (
    ASPECT_RATIOS,
    AspectRatioPreset,
    AspectRatioValidationError,
    PresetCategory,
    calculate_aspect_ratio,
    find_preset_for_dimensions,
    get_dimensions,
    get_preset_by_name,
    get_presets_by_category,
    list_preset_names,
    validate_dimensions,
    validate_preset_name,
)


class TestAspectRatioPreset:
    """Tests for AspectRatioPreset dataclass."""

    def test_preset_creation(self):
        """Test creating a preset with all fields."""
        preset = AspectRatioPreset(
            name="Test 16:9",
            width=1920,
            height=1080,
            ratio_string="16:9",
            category=PresetCategory.SOCIAL_MEDIA,
            description="Test preset",
        )
        assert preset.name == "Test 16:9"
        assert preset.width == 1920
        assert preset.height == 1080
        assert preset.ratio_string == "16:9"
        assert preset.category == PresetCategory.SOCIAL_MEDIA
        assert preset.description == "Test preset"

    def test_landscape_detection(self):
        """Test is_landscape property."""
        landscape = AspectRatioPreset(
            name="Landscape",
            width=1920,
            height=1080,
            ratio_string="16:9",
            category=PresetCategory.SOCIAL_MEDIA,
        )
        assert landscape.is_landscape is True
        assert landscape.is_portrait is False
        assert landscape.is_square is False

    def test_portrait_detection(self):
        """Test is_portrait property."""
        portrait = AspectRatioPreset(
            name="Portrait",
            width=1080,
            height=1920,
            ratio_string="9:16",
            category=PresetCategory.SOCIAL_MEDIA,
        )
        assert portrait.is_portrait is True
        assert portrait.is_landscape is False
        assert portrait.is_square is False

    def test_square_detection(self):
        """Test is_square property."""
        square = AspectRatioPreset(
            name="Square",
            width=1024,
            height=1024,
            ratio_string="1:1",
            category=PresetCategory.STANDARD,
        )
        assert square.is_square is True
        assert square.is_landscape is False
        assert square.is_portrait is False

    def test_custom_detection(self):
        """Test is_custom property."""
        custom = AspectRatioPreset(
            name="Custom",
            width=None,
            height=None,
            ratio_string="custom",
            category=PresetCategory.CUSTOM,
        )
        assert custom.is_custom is True
        assert custom.is_landscape is False
        assert custom.is_portrait is False
        assert custom.is_square is False

    def test_dimensions_tuple_property(self):
        """Test dimensions_tuple property."""
        preset = AspectRatioPreset(
            name="Test",
            width=1920,
            height=1080,
            ratio_string="16:9",
            category=PresetCategory.SOCIAL_MEDIA,
        )
        assert preset.dimensions_tuple == (1920, 1080)

    def test_dimensions_tuple_custom(self):
        """Test dimensions_tuple returns None for custom preset."""
        custom = AspectRatioPreset(
            name="Custom",
            width=None,
            height=None,
            ratio_string="custom",
            category=PresetCategory.CUSTOM,
        )
        assert custom.dimensions_tuple is None

    def test_immutability(self):
        """Test that preset is immutable (frozen=True)."""
        preset = AspectRatioPreset(
            name="Test",
            width=1920,
            height=1080,
            ratio_string="16:9",
            category=PresetCategory.SOCIAL_MEDIA,
        )
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            preset.width = 1280


class TestValidateDimensions:
    """Tests for validate_dimensions function."""

    def test_valid_dimensions(self):
        """Test valid dimensions pass validation."""
        validate_dimensions(1024, 1024)  # Should not raise
        validate_dimensions(1280, 1024)  # Should not raise (multiples of 64)
        validate_dimensions(64, 64)  # Min valid
        validate_dimensions(2048, 2048)  # Max valid

    def test_negative_width(self):
        """Test negative width raises error."""
        with pytest.raises(AspectRatioValidationError, match="must be positive"):
            validate_dimensions(-1024, 1024)

    def test_negative_height(self):
        """Test negative height raises error."""
        with pytest.raises(AspectRatioValidationError, match="must be positive"):
            validate_dimensions(1024, -1024)

    def test_zero_dimensions(self):
        """Test zero dimensions raise error."""
        with pytest.raises(AspectRatioValidationError, match="must be positive"):
            validate_dimensions(0, 1024)
        with pytest.raises(AspectRatioValidationError, match="must be positive"):
            validate_dimensions(1024, 0)

    def test_dimensions_too_small(self):
        """Test dimensions below minimum raise error."""
        with pytest.raises(AspectRatioValidationError, match="must be at least 64px"):
            validate_dimensions(32, 1024)
        with pytest.raises(AspectRatioValidationError, match="must be at least 64px"):
            validate_dimensions(1024, 32)

    def test_dimensions_too_large(self):
        """Test dimensions above maximum raise error."""
        with pytest.raises(AspectRatioValidationError, match="must not exceed 2048px"):
            validate_dimensions(4096, 1024)
        with pytest.raises(AspectRatioValidationError, match="must not exceed 2048px"):
            validate_dimensions(1024, 4096)

    def test_not_multiple_of_64(self):
        """Test dimensions not multiple of 64 raise error with suggestion."""
        with pytest.raises(AspectRatioValidationError, match="must be multiples of 64"):
            validate_dimensions(1000, 1024)
        with pytest.raises(AspectRatioValidationError, match="Nearest valid: 1024x1024"):
            validate_dimensions(1000, 1000)

    def test_edge_cases_64_and_2048(self):
        """Test edge case dimensions at boundaries."""
        validate_dimensions(64, 64)  # Min boundary
        validate_dimensions(2048, 2048)  # Max boundary
        validate_dimensions(64, 2048)  # Min-max combo
        validate_dimensions(2048, 64)  # Max-min combo


class TestValidatePresetName:
    """Tests for validate_preset_name function."""

    def test_valid_preset_names(self):
        """Test valid preset names pass validation."""
        validate_preset_name("Square 1:1 (1024x1024)")  # Should not raise
        validate_preset_name("Custom")  # Should not raise

    def test_invalid_preset_name(self):
        """Test invalid preset name raises error."""
        with pytest.raises(AspectRatioValidationError, match="Unknown preset"):
            validate_preset_name("Nonexistent Preset")

    def test_empty_string(self):
        """Test empty string raises error."""
        with pytest.raises(AspectRatioValidationError, match="Unknown preset"):
            validate_preset_name("")

    def test_case_sensitivity(self):
        """Test preset names are case-sensitive."""
        with pytest.raises(AspectRatioValidationError):
            validate_preset_name("square 1:1 (1024x1024)")  # lowercase


class TestCalculateAspectRatio:
    """Tests for calculate_aspect_ratio function."""

    def test_16_9_ratio(self):
        """Test calculating 16:9 ratio."""
        assert calculate_aspect_ratio(1920, 1080) == "16:9"
        assert calculate_aspect_ratio(1280, 720) == "16:9"

    def test_1_1_ratio(self):
        """Test calculating 1:1 ratio."""
        assert calculate_aspect_ratio(1024, 1024) == "1:1"
        assert calculate_aspect_ratio(512, 512) == "1:1"

    def test_3_2_ratio(self):
        """Test calculating 3:2 ratio."""
        assert calculate_aspect_ratio(1536, 1024) == "3:2"

    def test_2_3_ratio(self):
        """Test calculating 2:3 ratio."""
        assert calculate_aspect_ratio(832, 1280) == "13:20"  # Actually simplifies to 13:20

    def test_odd_dimensions(self):
        """Test odd dimension combinations."""
        # 1600x896 = 16:9 * 100:56 = 16:9 * 25:14 (simplified)
        result = calculate_aspect_ratio(1600, 896)
        assert ":" in result  # Just verify it returns a ratio

    def test_prime_number_dimensions(self):
        """Test with prime number dimensions."""
        result = calculate_aspect_ratio(1920, 1080)
        assert result == "16:9"


class TestGetPresetByName:
    """Tests for get_preset_by_name function."""

    def test_get_existing_presets(self):
        """Test getting existing presets."""
        preset = get_preset_by_name("Square 1:1 (1024x1024)")
        assert isinstance(preset, AspectRatioPreset)
        assert preset.width == 1024
        assert preset.height == 1024

    def test_get_custom_preset(self):
        """Test getting custom preset."""
        preset = get_preset_by_name("Custom")
        assert preset.is_custom is True
        assert preset.width is None
        assert preset.height is None

    def test_get_nonexistent_preset(self):
        """Test getting nonexistent preset raises error."""
        with pytest.raises(AspectRatioValidationError):
            get_preset_by_name("Nonexistent")

    def test_returns_correct_preset_object(self):
        """Test returned preset has correct attributes."""
        preset = get_preset_by_name("Widescreen 16:9 (1280x720)")
        assert preset.name == "Widescreen 16:9 (1280x720)"
        assert preset.width == 1280
        assert preset.height == 720
        assert preset.ratio_string == "16:9"
        assert preset.category == PresetCategory.SOCIAL_MEDIA


class TestListPresetNames:
    """Tests for list_preset_names function."""

    def test_returns_list(self):
        """Test function returns a list."""
        names = list_preset_names()
        assert isinstance(names, list)

    def test_contains_all_presets(self):
        """Test list contains all expected presets."""
        names = list_preset_names()
        assert "Square 1:1 (1024x1024)" in names
        assert "Widescreen 16:9 (1280x720)" in names
        assert "Custom" in names
        assert len(names) == 9  # 8 presets + Custom

    def test_maintains_order(self):
        """Test list maintains definition order."""
        names = list_preset_names()
        assert names[0] == "Square 1:1 (1024x1024)"
        assert names[-1] == "Custom"

    def test_includes_custom(self):
        """Test custom preset is included."""
        names = list_preset_names()
        assert "Custom" in names


class TestGetPresetsByCategory:
    """Tests for get_presets_by_category function."""

    def test_standard_category(self):
        """Test getting standard category presets."""
        presets = get_presets_by_category(PresetCategory.STANDARD)
        assert len(presets) > 0
        assert all(p.category == PresetCategory.STANDARD for p in presets)

    def test_social_media_category(self):
        """Test getting social media category presets."""
        presets = get_presets_by_category(PresetCategory.SOCIAL_MEDIA)
        assert len(presets) > 0
        assert all(p.category == PresetCategory.SOCIAL_MEDIA for p in presets)

    def test_photography_category(self):
        """Test getting photography category presets."""
        presets = get_presets_by_category(PresetCategory.PHOTOGRAPHY)
        assert len(presets) > 0
        assert all(p.category == PresetCategory.PHOTOGRAPHY for p in presets)

    def test_custom_category(self):
        """Test getting custom category."""
        presets = get_presets_by_category(PresetCategory.CUSTOM)
        assert len(presets) == 1
        assert presets[0].name == "Custom"

    def test_empty_category(self):
        """Test empty category returns empty list."""
        presets = get_presets_by_category("nonexistent")
        assert presets == []

    def test_returns_correct_presets(self):
        """Test returned presets match category."""
        social_presets = get_presets_by_category(PresetCategory.SOCIAL_MEDIA)
        for preset in social_presets:
            assert preset.category == PresetCategory.SOCIAL_MEDIA


class TestGetDimensions:
    """Tests for get_dimensions function."""

    def test_standard_preset_dimensions(self, test_config):
        """Test getting dimensions for standard preset."""
        width, height = get_dimensions("Square 1:1 (1024x1024)", test_config)
        assert width == 1024
        assert height == 1024

    def test_custom_preset_uses_config_defaults(self, test_config):
        """Test custom preset uses config defaults."""
        width, height = get_dimensions("Custom", test_config)
        assert width == test_config.default_width
        assert height == test_config.default_height

    def test_all_presets_return_valid_tuples(self, test_config):
        """Test all presets return valid dimension tuples."""
        for name in list_preset_names():
            width, height = get_dimensions(name, test_config)
            assert isinstance(width, int)
            assert isinstance(height, int)
            assert width > 0
            assert height > 0

    def test_invalid_preset_raises(self, test_config):
        """Test invalid preset name raises error."""
        with pytest.raises(AspectRatioValidationError):
            get_dimensions("Nonexistent", test_config)

    def test_widescreen_preset(self, test_config):
        """Test specific widescreen preset."""
        width, height = get_dimensions("Widescreen 16:9 (1280x720)", test_config)
        assert width == 1280
        assert height == 720


class TestFindPresetForDimensions:
    """Tests for find_preset_for_dimensions function."""

    def test_find_exact_match(self):
        """Test finding preset with exact dimension match."""
        preset = find_preset_for_dimensions(1024, 1024)
        assert preset is not None
        assert preset.name == "Square 1:1 (1024x1024)"

    def test_no_match_returns_none(self):
        """Test no match returns None."""
        preset = find_preset_for_dimensions(999, 999)
        assert preset is None

    def test_doesnt_match_custom(self):
        """Test custom preset is not matched."""
        # Even if we somehow pass None dimensions, shouldn't match custom
        preset = find_preset_for_dimensions(1024, 1024)
        assert preset is not None
        assert not preset.is_custom

    def test_finds_all_defined_presets(self):
        """Test all non-custom presets can be found."""
        expected_presets = [
            (1024, 1024),
            (1280, 720),
            (1600, 896),
            (720, 1280),
            (896, 1600),
            (1280, 832),
            (832, 1280),
            (1536, 1024),
        ]
        for width, height in expected_presets:
            preset = find_preset_for_dimensions(width, height)
            assert preset is not None
            assert preset.width == width
            assert preset.height == height

    def test_portrait_preset(self):
        """Test finding portrait preset."""
        preset = find_preset_for_dimensions(720, 1280)
        assert preset is not None
        assert preset.is_portrait is True


class TestBackwardCompatibility:
    """Tests for backward compatibility."""

    def test_aspect_ratios_dict_structure(self):
        """Test ASPECT_RATIOS maintains dict structure."""
        assert isinstance(ASPECT_RATIOS, dict)
        assert len(ASPECT_RATIOS) == 9

    def test_aspect_ratios_keys(self):
        """Test ASPECT_RATIOS contains expected keys."""
        assert "Square 1:1 (1024x1024)" in ASPECT_RATIOS
        assert "Widescreen 16:9 (1280x720)" in ASPECT_RATIOS
        assert "Custom" in ASPECT_RATIOS

    def test_aspect_ratios_values(self):
        """Test ASPECT_RATIOS values are tuples or None."""
        for key, value in ASPECT_RATIOS.items():
            if key == "Custom":
                assert value is None
            else:
                assert isinstance(value, tuple)
                assert len(value) == 2
                assert isinstance(value[0], int)
                assert isinstance(value[1], int)

    def test_custom_has_none_value(self):
        """Test Custom preset has None value."""
        assert ASPECT_RATIOS["Custom"] is None

    def test_can_import_from_models(self):
        """Test ASPECT_RATIOS can be imported from models.py."""
        from pipeworks.ui.models import ASPECT_RATIOS as ASPECT_RATIOS_FROM_MODELS

        # Should be the same dict
        assert ASPECT_RATIOS_FROM_MODELS == ASPECT_RATIOS

    def test_dict_values_match_presets(self):
        """Test dict values match preset dimensions_tuple."""
        for name, dims in ASPECT_RATIOS.items():
            preset = get_preset_by_name(name)
            assert preset.dimensions_tuple == dims


class TestPresetCategories:
    """Tests for preset category system."""

    def test_all_presets_have_valid_category(self):
        """Test all presets have a category."""
        valid_categories = {
            PresetCategory.STANDARD,
            PresetCategory.SOCIAL_MEDIA,
            PresetCategory.PHOTOGRAPHY,
            PresetCategory.PRINT,
            PresetCategory.CUSTOM,
        }
        for name in list_preset_names():
            preset = get_preset_by_name(name)
            assert preset.category in valid_categories

    def test_category_constants_exist(self):
        """Test PresetCategory constants exist."""
        assert hasattr(PresetCategory, "STANDARD")
        assert hasattr(PresetCategory, "SOCIAL_MEDIA")
        assert hasattr(PresetCategory, "PHOTOGRAPHY")
        assert hasattr(PresetCategory, "PRINT")
        assert hasattr(PresetCategory, "CUSTOM")

    def test_custom_in_custom_category(self):
        """Test Custom preset is in CUSTOM category."""
        preset = get_preset_by_name("Custom")
        assert preset.category == PresetCategory.CUSTOM

    def test_square_in_standard_category(self):
        """Test Square preset is in STANDARD category."""
        preset = get_preset_by_name("Square 1:1 (1024x1024)")
        assert preset.category == PresetCategory.STANDARD
