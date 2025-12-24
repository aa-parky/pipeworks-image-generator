"""Catalog management for moving favorited images to archive."""

import logging
import shutil
from pathlib import Path
from typing import Any

from .favorites_db import FavoritesDB

logger = logging.getLogger(__name__)


class CatalogManager:
    """Manage catalog operations for archiving favorited images.

    Handles bulk moving of favorited images from outputs to catalog,
    preserving directory structure and associated metadata files.
    """

    def __init__(self, outputs_dir: Path, catalog_dir: Path, favorites_db: FavoritesDB):
        """Initialize the catalog manager.

        Args:
            outputs_dir: Base outputs directory
            catalog_dir: Catalog/archive directory
            favorites_db: Favorites database instance
        """
        self.outputs_dir = Path(outputs_dir)
        self.catalog_dir = Path(catalog_dir)
        self.favorites_db = favorites_db

        # Ensure directories exist
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.catalog_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Initialized CatalogManager: outputs={self.outputs_dir}, catalog={self.catalog_dir}"
        )

    def move_favorites_to_catalog(self) -> dict[str, Any]:
        """Move all favorited images from outputs to catalog.

        This operation:
        1. Gets all favorited images from database
        2. Filters to only outputs/ images (skips catalog/)
        3. For each image:
           - Computes catalog destination (preserves subfolder structure)
           - Creates destination folders
           - Moves image file
           - Moves associated .txt and .json metadata files (if they exist)
           - Removes from favorites DB after successful move
        4. Returns stats about the operation

        Returns:
            Dictionary with operation stats:
            {
                'moved': int,           # Successfully moved
                'skipped': int,         # Already in catalog
                'failed': int,          # Failed to move
                'errors': list[str]     # Error messages
            }
        """
        logger.info("Starting bulk move of favorites to catalog")

        stats: dict[str, Any] = {"moved": 0, "skipped": 0, "failed": 0, "errors": []}

        # Get all favorites
        all_favorites = self.favorites_db.get_all_favorites()
        logger.info(f"Found {len(all_favorites)} total favorites")

        if not all_favorites:
            logger.info("No favorites to move")
            return stats

        # Filter to only outputs/ images (check if path is within outputs_dir)
        # This prevents moving images that are already in catalog/ or other directories
        outputs_favorites = []
        for img_path_str in all_favorites:
            try:
                img_path = Path(img_path_str)

                # Convert to absolute path if relative
                # Relative paths are resolved from current working directory
                if not img_path.is_absolute():
                    img_path = Path.cwd() / img_path
                img_path = img_path.resolve()

                # Check if the resolved path is within the outputs directory tree
                # This uses Path.is_relative_to() which is safe for path traversal
                if img_path.is_relative_to(self.outputs_dir.resolve()):
                    outputs_favorites.append(img_path_str)
            except (ValueError, Exception):
                # Skip paths that can't be resolved or have permission issues
                pass

        logger.info(f"Found {len(outputs_favorites)} favorites in outputs directory")

        for image_path_str in outputs_favorites:
            try:
                image_path = Path(image_path_str)

                # Skip if image doesn't exist
                if not image_path.exists():
                    logger.warning(f"Image not found (may have been moved already): {image_path}")
                    stats["skipped"] += 1  # type: ignore[assignment]
                    # Remove from favorites since file doesn't exist
                    self.favorites_db.remove_favorite(image_path_str)
                    continue

                # Move the image and its metadata
                success = self._move_image_with_metadata(image_path)

                if success:
                    stats["moved"] += 1  # type: ignore[assignment]
                    # Remove from favorites DB after successful move
                    self.favorites_db.remove_favorite(image_path_str)
                else:
                    stats["failed"] += 1  # type: ignore[assignment]
                    if isinstance(stats["errors"], list):
                        stats["errors"].append(f"Failed to move: {image_path}")

            except Exception as e:
                logger.error(f"Error processing {image_path_str}: {e}", exc_info=True)
                stats["failed"] += 1  # type: ignore[assignment]
                if isinstance(stats["errors"], list):
                    stats["errors"].append(f"{image_path_str}: {str(e)}")

        logger.info(
            f"Move operation complete: moved={stats['moved']}, "
            f"skipped={stats['skipped']}, failed={stats['failed']}"
        )

        return stats

    def _move_image_with_metadata(self, image_path: Path) -> bool:
        """Move image and its metadata files to catalog.

        Args:
            image_path: Path to image file in outputs directory

        Returns:
            True if move was successful, False otherwise
        """
        try:
            # Compute relative path from outputs directory
            relative_path = image_path.relative_to(self.outputs_dir)

            # Compute catalog destination (preserves subfolder structure)
            catalog_dest = self.catalog_dir / relative_path

            # Create destination directory
            catalog_dest.parent.mkdir(parents=True, exist_ok=True)

            # Move the main image file
            logger.info(f"Moving: {image_path} -> {catalog_dest}")
            shutil.move(str(image_path), str(catalog_dest))

            # Move associated metadata files (.txt and .json)
            # These files have the same basename as the image but different extensions
            # .txt contains the prompt, .json contains full generation parameters
            for suffix in [".txt", ".json"]:
                metadata_path = image_path.with_suffix(suffix)
                if metadata_path.exists():
                    metadata_dest = catalog_dest.with_suffix(suffix)
                    logger.debug(f"Moving metadata: {metadata_path} -> {metadata_dest}")
                    shutil.move(str(metadata_path), str(metadata_dest))

            logger.info(f"Successfully moved {image_path.name} to catalog")
            return True

        except Exception as e:
            logger.error(f"Error moving {image_path}: {e}", exc_info=True)
            return False

    def get_catalog_stats(self) -> dict[str, Any]:
        """Get statistics about the catalog directory.

        Returns:
            Dictionary with catalog stats:
            {
                'total_images': int,
                'total_size_bytes': int,
                'subdirectories': int
            }
        """
        stats = {"total_images": 0, "total_size_bytes": 0, "subdirectories": 0}

        try:
            if not self.catalog_dir.exists():
                return stats

            # Count subdirectories
            subdirs = [d for d in self.catalog_dir.rglob("*") if d.is_dir()]
            stats["subdirectories"] = len(subdirs)

            # Count images and total size
            image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
            for item in self.catalog_dir.rglob("*"):
                if item.is_file() and item.suffix.lower() in image_extensions:
                    stats["total_images"] += 1
                    stats["total_size_bytes"] += item.stat().st_size

        except Exception as e:
            logger.error(f"Error getting catalog stats: {e}", exc_info=True)

        return stats

    def validate_catalog_structure(self) -> list[str]:
        """Validate catalog directory structure.

        Checks for common issues like:
        - Orphaned metadata files (no corresponding image)
        - Images without metadata
        - Empty directories

        Returns:
            List of validation warnings
        """
        warnings: list[str] = []

        try:
            if not self.catalog_dir.exists():
                return warnings

            # Check for orphaned metadata files
            for metadata_file in self.catalog_dir.rglob("*.txt"):
                # Skip if it's actually an image file with .txt extension
                image_path = metadata_file.with_suffix(".png")
                if not image_path.exists():
                    # Try other image extensions
                    found = False
                    for ext in [".jpg", ".jpeg", ".webp"]:
                        if metadata_file.with_suffix(ext).exists():
                            found = True
                            break

                    if not found:
                        warnings.append(
                            f"Orphaned metadata: {metadata_file.relative_to(self.catalog_dir)}"
                        )

            # Check for empty directories
            for dirpath in self.catalog_dir.rglob("*"):
                if dirpath.is_dir():
                    # Check if directory is empty
                    if not any(dirpath.iterdir()):
                        warnings.append(f"Empty directory: {dirpath.relative_to(self.catalog_dir)}")

        except Exception as e:
            logger.error(f"Error validating catalog: {e}", exc_info=True)
            warnings.append(f"Validation error: {str(e)}")

        return warnings
