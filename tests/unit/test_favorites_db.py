"""Unit tests for FavoritesDB."""

import sqlite3
from pathlib import Path

from pipeworks.core.favorites_db import FavoritesDB


class TestFavoritesDB:
    """Tests for FavoritesDB class."""

    def test_initialization(self, temp_dir: Path):
        """Test database initialization creates file and schema."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        # Database file should exist
        assert db_path.exists()

        # Verify schema was created
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='favorites'")
            assert cursor.fetchone() is not None

            # Check index exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_favorited_at'"
            )
            assert cursor.fetchone() is not None

    def test_add_favorite(self, temp_dir: Path):
        """Test adding an image to favorites."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        result = db.add_favorite("outputs/test_image.png")

        assert result is True
        assert db.is_favorite("outputs/test_image.png") is True

    def test_add_favorite_already_exists(self, temp_dir: Path):
        """Test adding an already favorited image returns False."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        # Add first time
        result1 = db.add_favorite("outputs/test_image.png")
        assert result1 is True

        # Add second time
        result2 = db.add_favorite("outputs/test_image.png")
        assert result2 is False

        # Should still be favorited
        assert db.is_favorite("outputs/test_image.png") is True

    def test_remove_favorite(self, temp_dir: Path):
        """Test removing an image from favorites."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        # Add then remove
        db.add_favorite("outputs/test_image.png")
        result = db.remove_favorite("outputs/test_image.png")

        assert result is True
        assert db.is_favorite("outputs/test_image.png") is False

    def test_remove_favorite_not_exists(self, temp_dir: Path):
        """Test removing a non-favorited image returns False."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        result = db.remove_favorite("outputs/nonexistent.png")

        assert result is False

    def test_is_favorite_returns_false_for_new_db(self, temp_dir: Path):
        """Test is_favorite returns False for empty database."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        assert db.is_favorite("outputs/any_image.png") is False

    def test_is_favorite_returns_true_after_add(self, temp_dir: Path):
        """Test is_favorite returns True after adding."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        db.add_favorite("outputs/test_image.png")

        assert db.is_favorite("outputs/test_image.png") is True

    def test_get_all_favorites_empty(self, temp_dir: Path):
        """Test get_all_favorites returns empty list for new database."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        favorites = db.get_all_favorites()

        assert favorites == []

    def test_get_all_favorites_with_items(self, temp_dir: Path):
        """Test get_all_favorites returns all favorited images."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        # Add multiple favorites
        db.add_favorite("outputs/image1.png")
        db.add_favorite("outputs/image2.png")
        db.add_favorite("catalog/image3.png")

        favorites = db.get_all_favorites()

        assert len(favorites) == 3
        assert "outputs/image1.png" in favorites
        assert "outputs/image2.png" in favorites
        assert "catalog/image3.png" in favorites

    def test_get_all_favorites_sorted_by_date(self, temp_dir: Path):
        """Test get_all_favorites returns newest first."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        # Add in specific order
        db.add_favorite("outputs/image1.png")
        db.add_favorite("outputs/image2.png")
        db.add_favorite("outputs/image3.png")

        favorites = db.get_all_favorites()

        # Should be in reverse order (newest first)
        assert favorites[0] == "outputs/image3.png"
        assert favorites[1] == "outputs/image2.png"
        assert favorites[2] == "outputs/image1.png"

    def test_get_favorite_count_empty(self, temp_dir: Path):
        """Test get_favorite_count returns 0 for new database."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        count = db.get_favorite_count()

        assert count == 0

    def test_get_favorite_count_with_items(self, temp_dir: Path):
        """Test get_favorite_count returns correct count."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        db.add_favorite("outputs/image1.png")
        db.add_favorite("outputs/image2.png")
        db.add_favorite("outputs/image3.png")

        count = db.get_favorite_count()

        assert count == 3

    def test_clear_favorites(self, temp_dir: Path):
        """Test clear_favorites removes all favorites."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        # Add some favorites
        db.add_favorite("outputs/image1.png")
        db.add_favorite("outputs/image2.png")
        assert db.get_favorite_count() == 2

        # Clear all
        db.clear_favorites()

        assert db.get_favorite_count() == 0
        assert db.get_all_favorites() == []

    def test_toggle_favorite_adds_when_not_favorited(self, temp_dir: Path):
        """Test toggle_favorite adds when image is not favorited."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        result = db.toggle_favorite("outputs/test_image.png")

        assert result is True  # Now favorited
        assert db.is_favorite("outputs/test_image.png") is True

    def test_toggle_favorite_removes_when_favorited(self, temp_dir: Path):
        """Test toggle_favorite removes when image is already favorited."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        # Add first
        db.add_favorite("outputs/test_image.png")

        # Toggle should remove
        result = db.toggle_favorite("outputs/test_image.png")

        assert result is False  # Now unfavorited
        assert db.is_favorite("outputs/test_image.png") is False

    def test_toggle_favorite_multiple_times(self, temp_dir: Path):
        """Test toggle_favorite works correctly when called multiple times."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        # Toggle on
        result1 = db.toggle_favorite("outputs/test_image.png")
        assert result1 is True

        # Toggle off
        result2 = db.toggle_favorite("outputs/test_image.png")
        assert result2 is False

        # Toggle on again
        result3 = db.toggle_favorite("outputs/test_image.png")
        assert result3 is True

    def test_path_normalization_absolute_path(self, temp_dir: Path):
        """Test that absolute paths are normalized."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        # Create an absolute path
        absolute_path = Path.cwd() / "outputs" / "test_image.png"

        db.add_favorite(str(absolute_path))

        # Should be able to query with relative path
        assert db.is_favorite("outputs/test_image.png") is True

    def test_path_normalization_path_object(self, temp_dir: Path):
        """Test that Path objects are handled correctly."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        # Use Path object
        path = Path("outputs") / "test_image.png"

        db.add_favorite(path)

        assert db.is_favorite(path) is True
        assert db.is_favorite("outputs/test_image.png") is True

    def test_path_normalization_forward_slashes(self, temp_dir: Path):
        """Test that paths are normalized to forward slashes."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        # Add with backslashes (Windows-style)
        db.add_favorite("outputs\\test_image.png")

        # Should be stored with forward slashes
        favorites = db.get_all_favorites()
        assert "outputs/test_image.png" in favorites

    def test_multiple_images_in_different_directories(self, temp_dir: Path):
        """Test handling images from different directories."""
        db_path = temp_dir / "test_favorites.db"
        db = FavoritesDB(db_path)

        db.add_favorite("outputs/2024-12-16/image1.png")
        db.add_favorite("outputs/2024-12-17/image2.png")
        db.add_favorite("catalog/archive/image3.png")

        assert db.get_favorite_count() == 3
        assert db.is_favorite("outputs/2024-12-16/image1.png") is True
        assert db.is_favorite("outputs/2024-12-17/image2.png") is True
        assert db.is_favorite("catalog/archive/image3.png") is True

    def test_database_persistence(self, temp_dir: Path):
        """Test that favorites persist across database instances."""
        db_path = temp_dir / "test_favorites.db"

        # Create first instance and add favorite
        db1 = FavoritesDB(db_path)
        db1.add_favorite("outputs/test_image.png")

        # Create second instance
        db2 = FavoritesDB(db_path)

        # Should see the same favorite
        assert db2.is_favorite("outputs/test_image.png") is True
        assert db2.get_favorite_count() == 1

    def test_database_in_subdirectory(self, temp_dir: Path):
        """Test database creation in nested directory."""
        db_path = temp_dir / "subdir" / "nested" / "favorites.db"
        db = FavoritesDB(db_path)

        # Parent directories should be created
        assert db_path.parent.exists()
        assert db_path.exists()

        # Database should work normally
        db.add_favorite("outputs/test.png")
        assert db.is_favorite("outputs/test.png") is True
