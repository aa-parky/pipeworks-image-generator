"""Unit tests for CatalogManager."""

import pytest
from pathlib import Path

from pipeworks.core.catalog_manager import CatalogManager
from pipeworks.core.favorites_db import FavoritesDB


class TestCatalogManager:
    """Tests for CatalogManager class."""

    def test_initialization(self, temp_dir: Path):
        """Test catalog manager initialization."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        favorites_db = FavoritesDB(db_path)
        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)

        assert manager.outputs_dir == outputs_dir
        assert manager.catalog_dir == catalog_dir
        assert manager.favorites_db == favorites_db

        # Directories should be created
        assert outputs_dir.exists()
        assert catalog_dir.exists()

    def test_move_favorites_empty_database(self, temp_dir: Path):
        """Test moving favorites when database is empty."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        favorites_db = FavoritesDB(db_path)
        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)

        stats = manager.move_favorites_to_catalog()

        assert stats["moved"] == 0
        assert stats["skipped"] == 0
        assert stats["failed"] == 0
        assert stats["errors"] == []

    def test_move_single_image(self, temp_dir: Path):
        """Test moving a single favorited image."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        # Create test image
        test_image = outputs_dir / "test_image.png"
        test_image.write_text("fake image data")

        # Add to favorites
        favorites_db = FavoritesDB(db_path)
        favorites_db.add_favorite(str(test_image))

        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)
        stats = manager.move_favorites_to_catalog()

        # Check stats
        assert stats["moved"] == 1
        assert stats["failed"] == 0

        # Check image was moved
        assert not test_image.exists()
        assert (catalog_dir / "test_image.png").exists()

        # Check removed from favorites
        assert not favorites_db.is_favorite(str(test_image))

    def test_move_image_with_metadata(self, temp_dir: Path):
        """Test moving image with .txt and .json metadata files."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        # Create test image with metadata
        test_image = outputs_dir / "test_image.png"
        test_txt = outputs_dir / "test_image.txt"
        test_json = outputs_dir / "test_image.json"

        test_image.write_text("fake image")
        test_txt.write_text("test prompt")
        test_json.write_text('{"seed": 42}')

        # Add to favorites
        favorites_db = FavoritesDB(db_path)
        favorites_db.add_favorite(str(test_image))

        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)
        stats = manager.move_favorites_to_catalog()

        # Check all files were moved
        assert not test_image.exists()
        assert not test_txt.exists()
        assert not test_json.exists()

        assert (catalog_dir / "test_image.png").exists()
        assert (catalog_dir / "test_image.txt").exists()
        assert (catalog_dir / "test_image.json").exists()

        # Check metadata content
        assert (catalog_dir / "test_image.txt").read_text() == "test prompt"
        assert (catalog_dir / "test_image.json").read_text() == '{"seed": 42}'

        assert stats["moved"] == 1

    def test_move_image_with_partial_metadata(self, temp_dir: Path):
        """Test moving image with only .txt metadata (no .json)."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        # Create test image with only .txt metadata
        test_image = outputs_dir / "test_image.png"
        test_txt = outputs_dir / "test_image.txt"

        test_image.write_text("fake image")
        test_txt.write_text("test prompt")

        favorites_db = FavoritesDB(db_path)
        favorites_db.add_favorite(str(test_image))

        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)
        stats = manager.move_favorites_to_catalog()

        # Image and .txt moved, .json doesn't exist
        assert (catalog_dir / "test_image.png").exists()
        assert (catalog_dir / "test_image.txt").exists()
        assert not (catalog_dir / "test_image.json").exists()

        assert stats["moved"] == 1

    def test_preserve_subfolder_structure(self, temp_dir: Path):
        """Test that subfolder structure is preserved when moving."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        # Create nested directory structure
        subdir = outputs_dir / "2024-12-16"
        subdir.mkdir()
        test_image = subdir / "test_image.png"
        test_image.write_text("fake image")

        favorites_db = FavoritesDB(db_path)
        favorites_db.add_favorite(str(test_image))

        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)
        stats = manager.move_favorites_to_catalog()

        # Check preserved structure
        assert not test_image.exists()
        assert (catalog_dir / "2024-12-16" / "test_image.png").exists()

        assert stats["moved"] == 1

    def test_preserve_deep_nested_structure(self, temp_dir: Path):
        """Test preservation of deeply nested directory structures."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        # Create deeply nested structure
        deep_dir = outputs_dir / "2024" / "12" / "16" / "session1"
        deep_dir.mkdir(parents=True)
        test_image = deep_dir / "test_image.png"
        test_image.write_text("fake image")

        favorites_db = FavoritesDB(db_path)
        favorites_db.add_favorite(str(test_image))

        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)
        stats = manager.move_favorites_to_catalog()

        # Check deeply nested structure preserved
        expected_path = catalog_dir / "2024" / "12" / "16" / "session1" / "test_image.png"
        assert expected_path.exists()
        assert stats["moved"] == 1

    def test_move_multiple_images(self, temp_dir: Path):
        """Test moving multiple favorited images."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        # Create multiple test images
        for i in range(5):
            test_image = outputs_dir / f"test_image_{i}.png"
            test_image.write_text(f"fake image {i}")

        favorites_db = FavoritesDB(db_path)

        # Favorite all images
        for i in range(5):
            favorites_db.add_favorite(str(outputs_dir / f"test_image_{i}.png"))

        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)
        stats = manager.move_favorites_to_catalog()

        # Check all moved
        assert stats["moved"] == 5
        assert stats["failed"] == 0

        # Verify all in catalog
        for i in range(5):
            assert (catalog_dir / f"test_image_{i}.png").exists()
            assert not (outputs_dir / f"test_image_{i}.png").exists()

    def test_skip_catalog_images(self, temp_dir: Path):
        """Test that images already in catalog are skipped."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        # Create image in catalog
        catalog_image = catalog_dir / "catalog_image.png"
        catalog_image.write_text("catalog image")

        favorites_db = FavoritesDB(db_path)
        favorites_db.add_favorite(str(catalog_image))

        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)
        stats = manager.move_favorites_to_catalog()

        # Should be skipped (no error, not moved)
        assert stats["moved"] == 0
        assert catalog_image.exists()

    def test_handle_missing_image(self, temp_dir: Path):
        """Test handling of favorited image that doesn't exist."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        # Favorite non-existent image
        favorites_db = FavoritesDB(db_path)
        fake_image = outputs_dir / "nonexistent.png"
        favorites_db.add_favorite(str(fake_image))

        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)
        stats = manager.move_favorites_to_catalog()

        # Should be skipped and removed from favorites
        assert stats["skipped"] == 1
        assert not favorites_db.is_favorite(str(fake_image))

    def test_get_catalog_stats_empty(self, temp_dir: Path):
        """Test getting stats for empty catalog."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        favorites_db = FavoritesDB(db_path)
        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)

        stats = manager.get_catalog_stats()

        assert stats["total_images"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["subdirectories"] == 0

    def test_get_catalog_stats_with_images(self, temp_dir: Path):
        """Test getting stats for catalog with images."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        # Create images in catalog
        (catalog_dir / "subdir").mkdir()
        img1 = catalog_dir / "image1.png"
        img2 = catalog_dir / "subdir" / "image2.png"

        img1.write_text("x" * 100)  # 100 bytes
        img2.write_text("y" * 200)  # 200 bytes

        favorites_db = FavoritesDB(db_path)
        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)

        stats = manager.get_catalog_stats()

        assert stats["total_images"] == 2
        assert stats["total_size_bytes"] == 300
        assert stats["subdirectories"] == 1

    def test_validate_catalog_structure(self, temp_dir: Path):
        """Test catalog validation with no issues."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        # Create valid catalog structure
        img = catalog_dir / "image.png"
        txt = catalog_dir / "image.txt"
        json_file = catalog_dir / "image.json"

        img.write_text("image")
        txt.write_text("prompt")
        json_file.write_text("{}")

        favorites_db = FavoritesDB(db_path)
        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)

        warnings = manager.validate_catalog_structure()

        assert len(warnings) == 0

    def test_validate_detects_orphaned_metadata(self, temp_dir: Path):
        """Test validation detects metadata without images."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        # Create orphaned metadata
        orphan_txt = catalog_dir / "orphan.txt"
        orphan_txt.write_text("orphaned prompt")

        favorites_db = FavoritesDB(db_path)
        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)

        warnings = manager.validate_catalog_structure()

        assert len(warnings) > 0
        assert any("Orphaned metadata" in w for w in warnings)

    def test_validate_detects_empty_directories(self, temp_dir: Path):
        """Test validation detects empty directories."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        # Create empty subdirectory
        empty_dir = catalog_dir / "empty_folder"
        empty_dir.mkdir()

        favorites_db = FavoritesDB(db_path)
        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)

        warnings = manager.validate_catalog_structure()

        assert len(warnings) > 0
        assert any("Empty directory" in w for w in warnings)

    def test_move_mixed_success_and_failure(self, temp_dir: Path):
        """Test move operation with some successes and some failures."""
        outputs_dir = temp_dir / "outputs"
        catalog_dir = temp_dir / "catalog"
        db_path = temp_dir / "favorites.db"

        outputs_dir.mkdir()
        catalog_dir.mkdir()

        # Create one valid image
        valid_image = outputs_dir / "valid.png"
        valid_image.write_text("valid")

        favorites_db = FavoritesDB(db_path)
        favorites_db.add_favorite(str(valid_image))

        # Favorite a missing image
        missing_image = outputs_dir / "missing.png"
        favorites_db.add_favorite(str(missing_image))

        manager = CatalogManager(outputs_dir, catalog_dir, favorites_db)
        stats = manager.move_favorites_to_catalog()

        # One moved, one skipped
        assert stats["moved"] == 1
        assert stats["skipped"] == 1
        assert (catalog_dir / "valid.png").exists()
