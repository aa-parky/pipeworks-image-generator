"""Unit tests for GalleryBrowser functionality."""

import json
from pathlib import Path

from pipeworks.core.gallery_browser import GalleryBrowser


class TestGalleryBrowserInit:
    """Tests for GalleryBrowser initialization."""

    def test_init_with_outputs_only(self, temp_dir):
        """Test initialization with only outputs directory."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)

        assert browser.outputs_dir == outputs_dir
        assert browser.catalog_dir is None
        assert browser.current_root == outputs_dir

    def test_init_with_both_directories(self, temp_dir):
        """Test initialization with both outputs and catalog directories."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        outputs_dir.mkdir()
        catalog_dir.mkdir()

        browser = GalleryBrowser(outputs_dir, catalog_dir)

        assert browser.outputs_dir == outputs_dir
        assert browser.catalog_dir == catalog_dir
        assert browser.current_root == outputs_dir

    def test_init_creates_missing_outputs_dir(self, temp_dir):
        """Test that initialization creates missing outputs directory."""
        outputs_dir = temp_dir / "outputs"

        browser = GalleryBrowser(outputs_dir)

        assert outputs_dir.exists()
        assert browser.outputs_dir == outputs_dir

    def test_init_creates_missing_catalog_dir(self, temp_dir):
        """Test that initialization creates missing catalog directory."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir, catalog_dir)

        assert catalog_dir.exists()
        assert browser.catalog_dir == catalog_dir

    def test_init_with_path_objects(self, temp_dir):
        """Test initialization with Path objects."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir, catalog_dir)

        assert isinstance(browser.outputs_dir, Path)
        assert isinstance(browser.catalog_dir, Path)


class TestGalleryBrowserRootManagement:
    """Tests for root directory management."""

    def test_get_root_choices_outputs_only(self, temp_dir):
        """Test getting root choices with only outputs."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)
        choices = browser.get_root_choices()

        assert choices == ["📁 outputs"]

    def test_get_root_choices_with_catalog(self, temp_dir):
        """Test getting root choices with catalog."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        outputs_dir.mkdir()
        catalog_dir.mkdir()

        browser = GalleryBrowser(outputs_dir, catalog_dir)
        choices = browser.get_root_choices()

        assert choices == ["📁 outputs", "📁 catalog"]

    def test_set_root_to_outputs(self, temp_dir):
        """Test switching to outputs root."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        outputs_dir.mkdir()
        catalog_dir.mkdir()

        browser = GalleryBrowser(outputs_dir, catalog_dir)
        browser.set_root("outputs")

        assert browser.current_root == outputs_dir

    def test_set_root_to_catalog(self, temp_dir):
        """Test switching to catalog root."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        outputs_dir.mkdir()
        catalog_dir.mkdir()

        browser = GalleryBrowser(outputs_dir, catalog_dir)
        browser.set_root("catalog")

        assert browser.current_root == catalog_dir

    def test_set_root_with_emoji_prefix(self, temp_dir):
        """Test switching root with emoji prefix."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        outputs_dir.mkdir()
        catalog_dir.mkdir()

        browser = GalleryBrowser(outputs_dir, catalog_dir)
        browser.set_root("📁 catalog")

        assert browser.current_root == catalog_dir

    def test_set_root_invalid_name(self, temp_dir):
        """Test setting root with invalid name."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)
        original_root = browser.current_root
        browser.set_root("invalid")

        # Root should remain unchanged
        assert browser.current_root == original_root

    def test_set_root_catalog_without_catalog_dir(self, temp_dir):
        """Test setting root to catalog when catalog_dir is None."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)
        browser.set_root("catalog")

        # Should remain at outputs
        assert browser.current_root == outputs_dir

    def test_get_current_root_name_outputs(self, temp_dir):
        """Test getting current root name when on outputs."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)

        assert browser.get_current_root_name() == "outputs"

    def test_get_current_root_name_catalog(self, temp_dir):
        """Test getting current root name when on catalog."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        outputs_dir.mkdir()
        catalog_dir.mkdir()

        browser = GalleryBrowser(outputs_dir, catalog_dir)
        browser.set_root("catalog")

        assert browser.get_current_root_name() == "catalog"


class TestGalleryBrowserPathValidation:
    """Tests for path validation (security)."""

    def test_validate_path_empty_string(self, temp_dir):
        """Test that empty path is valid."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)

        assert browser.validate_path("") is True

    def test_validate_path_simple_subdir(self, temp_dir):
        """Test validating simple subdirectory."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        subdir = outputs_dir / "subfolder"
        subdir.mkdir()

        browser = GalleryBrowser(outputs_dir)

        assert browser.validate_path("subfolder") is True

    def test_validate_path_nested_subdir(self, temp_dir):
        """Test validating nested subdirectory."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        (outputs_dir / "a" / "b" / "c").mkdir(parents=True)

        browser = GalleryBrowser(outputs_dir)

        assert browser.validate_path("a/b/c") is True

    def test_validate_path_traversal_attack(self, temp_dir):
        """Test that path traversal is rejected."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)

        # Try to escape with ../
        assert browser.validate_path("../../../etc/passwd") is False

    def test_validate_path_traversal_with_valid_prefix(self, temp_dir):
        """Test path traversal attack with valid-looking prefix."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        subdir = outputs_dir / "valid"
        subdir.mkdir()

        browser = GalleryBrowser(outputs_dir)

        # Try to escape even with valid prefix
        assert browser.validate_path("valid/../../etc/passwd") is False

    def test_validate_path_nonexistent_but_valid(self, temp_dir):
        """Test that nonexistent paths can be valid."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)

        # Path doesn't exist but is within root
        assert browser.validate_path("nonexistent/path") is True


class TestGalleryBrowserFileScanning:
    """Tests for file and directory scanning."""

    def test_get_items_in_path_empty_dir(self, temp_dir):
        """Test getting items in empty directory."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)
        folders, images = browser.get_items_in_path("")

        assert folders == []
        assert images == []

    def test_get_items_in_path_with_images(self, temp_dir):
        """Test getting items with images at root."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        (outputs_dir / "image1.png").touch()
        (outputs_dir / "image2.jpg").touch()

        browser = GalleryBrowser(outputs_dir)
        folders, images = browser.get_items_in_path("")

        assert folders == []
        assert sorted(images) == ["image1.png", "image2.jpg"]

    def test_get_items_in_path_with_folders(self, temp_dir):
        """Test getting items with folders containing images."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        folder1 = outputs_dir / "folder1"
        folder1.mkdir()
        (folder1 / "image.png").touch()

        browser = GalleryBrowser(outputs_dir)
        folders, images = browser.get_items_in_path("")

        assert folders == ["folder1"]
        assert images == []

    def test_get_items_in_path_mixed_content(self, temp_dir):
        """Test getting items with both folders and images."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        (outputs_dir / "image1.png").touch()
        folder1 = outputs_dir / "folder1"
        folder1.mkdir()
        (folder1 / "nested.png").touch()

        browser = GalleryBrowser(outputs_dir)
        folders, images = browser.get_items_in_path("")

        assert folders == ["folder1"]
        assert images == ["image1.png"]

    def test_get_items_in_path_skips_empty_folders(self, temp_dir):
        """Test that empty folders are not included."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        (outputs_dir / "empty_folder").mkdir()

        browser = GalleryBrowser(outputs_dir)
        folders, images = browser.get_items_in_path("")

        assert folders == []
        assert images == []

    def test_get_items_in_path_various_image_formats(self, temp_dir):
        """Test getting items with various image formats."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        (outputs_dir / "image.png").touch()
        (outputs_dir / "photo.jpg").touch()
        (outputs_dir / "picture.jpeg").touch()
        (outputs_dir / "web.webp").touch()

        browser = GalleryBrowser(outputs_dir)
        folders, images = browser.get_items_in_path("")

        assert len(images) == 4
        assert "image.png" in images
        assert "photo.jpg" in images
        assert "picture.jpeg" in images
        assert "web.webp" in images

    def test_get_items_in_path_filters_non_images(self, temp_dir):
        """Test that non-image files are filtered out."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        (outputs_dir / "image.png").touch()
        (outputs_dir / "data.txt").touch()
        (outputs_dir / "metadata.json").touch()

        browser = GalleryBrowser(outputs_dir)
        folders, images = browser.get_items_in_path("")

        assert images == ["image.png"]

    def test_get_items_in_path_in_subdirectory(self, temp_dir):
        """Test getting items in subdirectory."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        subdir = outputs_dir / "subfolder"
        subdir.mkdir()
        (subdir / "nested.png").touch()

        browser = GalleryBrowser(outputs_dir)
        folders, images = browser.get_items_in_path("subfolder")

        assert folders == []
        assert images == ["nested.png"]

    def test_get_items_in_path_invalid_path(self, temp_dir):
        """Test getting items with invalid path."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)
        folders, images = browser.get_items_in_path("../../../etc")

        assert folders == []
        assert images == []

    def test_get_items_in_path_nonexistent_path(self, temp_dir):
        """Test getting items in nonexistent path."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)
        folders, images = browser.get_items_in_path("nonexistent")

        assert folders == []
        assert images == []

    def test_scan_images_empty_dir(self, temp_dir):
        """Test scanning images in empty directory."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)
        images = browser.scan_images("")

        assert images == []

    def test_scan_images_with_images(self, temp_dir):
        """Test scanning images returns full paths."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        (outputs_dir / "image1.png").touch()
        (outputs_dir / "image2.png").touch()

        browser = GalleryBrowser(outputs_dir)
        images = browser.scan_images("")

        assert len(images) == 2
        assert all(str(outputs_dir) in img for img in images)
        assert any("image1.png" in img for img in images)
        assert any("image2.png" in img for img in images)

    def test_scan_images_sorted(self, temp_dir):
        """Test that scanned images are sorted."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        (outputs_dir / "c.png").touch()
        (outputs_dir / "a.png").touch()
        (outputs_dir / "b.png").touch()

        browser = GalleryBrowser(outputs_dir)
        images = browser.scan_images("")

        # Extract filenames and check they're sorted
        filenames = [Path(img).name for img in images]
        assert filenames == ["a.png", "b.png", "c.png"]

    def test_scan_images_invalid_path(self, temp_dir):
        """Test scanning images with invalid path."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)
        images = browser.scan_images("../../../etc")

        assert images == []

    def test_scan_images_in_subdirectory(self, temp_dir):
        """Test scanning images in subdirectory."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        subdir = outputs_dir / "subfolder"
        subdir.mkdir()
        (subdir / "nested.png").touch()

        browser = GalleryBrowser(outputs_dir)
        images = browser.scan_images("subfolder")

        assert len(images) == 1
        assert "nested.png" in images[0]

    def test_get_image_count(self, temp_dir):
        """Test getting image count."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        (outputs_dir / "image1.png").touch()
        (outputs_dir / "image2.png").touch()
        (outputs_dir / "image3.png").touch()

        browser = GalleryBrowser(outputs_dir)
        count = browser.get_image_count("")

        assert count == 3

    def test_get_image_count_empty(self, temp_dir):
        """Test getting image count in empty directory."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)
        count = browser.get_image_count("")

        assert count == 0


class TestGalleryBrowserMetadataReading:
    """Tests for metadata file reading."""

    def test_read_txt_metadata_exists(self, temp_dir):
        """Test reading existing .txt metadata."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        image_path = outputs_dir / "image.png"
        txt_path = outputs_dir / "image.txt"
        image_path.touch()
        txt_path.write_text("A test prompt", encoding="utf-8")

        browser = GalleryBrowser(outputs_dir)
        content = browser.read_txt_metadata(str(image_path))

        assert content == "A test prompt"

    def test_read_txt_metadata_not_exists(self, temp_dir):
        """Test reading non-existent .txt metadata."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        image_path = outputs_dir / "image.png"
        image_path.touch()

        browser = GalleryBrowser(outputs_dir)
        content = browser.read_txt_metadata(str(image_path))

        assert content is None

    def test_read_txt_metadata_with_unicode(self, temp_dir):
        """Test reading .txt metadata with unicode characters."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        image_path = outputs_dir / "image.png"
        txt_path = outputs_dir / "image.txt"
        image_path.touch()
        txt_path.write_text("🎨 A prompt with émojis and àccents", encoding="utf-8")

        browser = GalleryBrowser(outputs_dir)
        content = browser.read_txt_metadata(str(image_path))

        assert content == "🎨 A prompt with émojis and àccents"

    def test_read_json_metadata_exists(self, temp_dir):
        """Test reading existing .json metadata."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        image_path = outputs_dir / "image.png"
        json_path = outputs_dir / "image.json"
        image_path.touch()

        metadata = {"prompt": "test", "seed": 42, "width": 1024}
        json_path.write_text(json.dumps(metadata), encoding="utf-8")

        browser = GalleryBrowser(outputs_dir)
        data = browser.read_json_metadata(str(image_path))

        assert data == metadata

    def test_read_json_metadata_not_exists(self, temp_dir):
        """Test reading non-existent .json metadata."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        image_path = outputs_dir / "image.png"
        image_path.touch()

        browser = GalleryBrowser(outputs_dir)
        data = browser.read_json_metadata(str(image_path))

        assert data is None

    def test_read_json_metadata_with_nested_data(self, temp_dir):
        """Test reading .json metadata with nested structures."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        image_path = outputs_dir / "image.png"
        json_path = outputs_dir / "image.json"
        image_path.touch()

        metadata = {
            "prompt": "test",
            "params": {"seed": 42, "steps": 9},
            "tags": ["tag1", "tag2"],
        }
        json_path.write_text(json.dumps(metadata), encoding="utf-8")

        browser = GalleryBrowser(outputs_dir)
        data = browser.read_json_metadata(str(image_path))

        assert data == metadata


class TestGalleryBrowserMetadataFormatting:
    """Tests for metadata formatting."""

    def test_format_metadata_txt_with_content(self, temp_dir):
        """Test formatting .txt metadata with content."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)
        formatted = browser.format_metadata_txt("A test prompt", "image.png")

        assert "image.png" in formatted
        assert "A test prompt" in formatted
        assert "**Prompt:**" in formatted

    def test_format_metadata_txt_none(self, temp_dir):
        """Test formatting when .txt metadata is None."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)
        formatted = browser.format_metadata_txt(None, "image.png")

        assert "image.png" in formatted
        assert "No .txt metadata found" in formatted

    def test_format_metadata_json_with_data(self, temp_dir):
        """Test formatting .json metadata with data."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        metadata = {
            "prompt": "test prompt",
            "width": 1024,
            "height": 1024,
            "seed": 42,
        }

        browser = GalleryBrowser(outputs_dir)
        formatted = browser.format_metadata_json(metadata, "image.png")

        assert "image.png" in formatted
        assert "test prompt" in formatted
        assert "1024" in formatted
        assert "42" in formatted
        # Should be a markdown table
        assert "|" in formatted
        assert "Parameter" in formatted
        assert "Value" in formatted

    def test_format_metadata_json_none(self, temp_dir):
        """Test formatting when .json metadata is None."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        browser = GalleryBrowser(outputs_dir)
        formatted = browser.format_metadata_json(None, "image.png")

        assert "image.png" in formatted
        assert "No .json metadata found" in formatted

    def test_format_metadata_json_truncates_long_prompt(self, temp_dir):
        """Test that long prompts are truncated in JSON formatting."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        long_prompt = "A" * 150
        metadata = {"prompt": long_prompt}

        browser = GalleryBrowser(outputs_dir)
        formatted = browser.format_metadata_json(metadata, "image.png")

        # Should truncate to 100 chars + "..."
        assert "A" * 100 in formatted
        assert "..." in formatted
        assert long_prompt not in formatted

    def test_format_metadata_json_with_all_key_fields(self, temp_dir):
        """Test formatting with all standard key fields."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        metadata = {
            "prompt": "test",
            "width": 1024,
            "height": 768,
            "num_inference_steps": 9,
            "seed": 42,
            "guidance_scale": 0.0,
            "model_id": "test-model",
            "timestamp": "2024-01-01T00:00:00",
        }

        browser = GalleryBrowser(outputs_dir)
        formatted = browser.format_metadata_json(metadata, "image.png")

        # All fields should be present
        for key, value in metadata.items():
            assert str(value) in formatted

    def test_format_metadata_json_with_extra_fields(self, temp_dir):
        """Test formatting with extra fields beyond standard ones."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()

        metadata = {
            "prompt": "test",
            "custom_field": "custom_value",
            "another_field": 123,
        }

        browser = GalleryBrowser(outputs_dir)
        formatted = browser.format_metadata_json(metadata, "image.png")

        # All fields should be present
        assert "custom_field" in formatted
        assert "custom_value" in formatted
        assert "another_field" in formatted
        assert "123" in formatted


class TestGalleryBrowserRootSwitching:
    """Tests for switching between outputs and catalog roots."""

    def test_scan_images_switches_roots(self, temp_dir):
        """Test that scanning respects current root."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        outputs_dir.mkdir()
        catalog_dir.mkdir()
        (outputs_dir / "outputs_image.png").touch()
        (catalog_dir / "catalog_image.png").touch()

        browser = GalleryBrowser(outputs_dir, catalog_dir)

        # Scan in outputs
        images_outputs = browser.scan_images("")
        assert len(images_outputs) == 1
        assert "outputs_image.png" in images_outputs[0]

        # Switch to catalog
        browser.set_root("catalog")
        images_catalog = browser.scan_images("")
        assert len(images_catalog) == 1
        assert "catalog_image.png" in images_catalog[0]

    def test_validate_path_respects_current_root(self, temp_dir):
        """Test that path validation respects current root."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        outputs_dir.mkdir()
        catalog_dir.mkdir()

        browser = GalleryBrowser(outputs_dir, catalog_dir)

        # Initially on outputs
        assert browser.current_root == outputs_dir

        # Switch to catalog
        browser.set_root("catalog")
        assert browser.current_root == catalog_dir

        # Validation should be relative to catalog now
        assert browser.validate_path("") is True


class TestGalleryBrowserEdgeCases:
    """Tests for edge cases and error handling."""

    def test_case_insensitive_image_extensions(self, temp_dir):
        """Test that image extensions are case-insensitive."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        (outputs_dir / "image.PNG").touch()
        (outputs_dir / "photo.JPG").touch()
        (outputs_dir / "picture.JpEg").touch()

        browser = GalleryBrowser(outputs_dir)
        folders, images = browser.get_items_in_path("")

        assert len(images) == 3

    def test_folders_with_deeply_nested_images(self, temp_dir):
        """Test that folders with deeply nested images are detected."""
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        deep_path = outputs_dir / "a" / "b" / "c" / "d"
        deep_path.mkdir(parents=True)
        (deep_path / "deep.png").touch()

        browser = GalleryBrowser(outputs_dir)
        folders, images = browser.get_items_in_path("")

        # Folder "a" should be included because it contains images (deeply nested)
        assert "a" in folders
