"""Gallery browser utility for viewing generated images and metadata."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class GalleryBrowser:
    """Browse generated images and their metadata in the outputs and catalog directories."""

    def __init__(self, outputs_dir: Path, catalog_dir: Path | None = None):
        """
        Initialize the gallery browser.

        Args:
            outputs_dir: Base directory containing generated images
            catalog_dir: Optional catalog directory for archived images
        """
        self.outputs_dir = Path(outputs_dir)
        self.catalog_dir = Path(catalog_dir) if catalog_dir else None
        self.current_root = self.outputs_dir  # Start with outputs as default

        if not self.outputs_dir.exists():
            logger.warning(f"Outputs directory does not exist: {self.outputs_dir}")
            self.outputs_dir.mkdir(parents=True, exist_ok=True)

        if self.catalog_dir and not self.catalog_dir.exists():
            logger.info(f"Creating catalog directory: {self.catalog_dir}")
            self.catalog_dir.mkdir(parents=True, exist_ok=True)

    def get_root_choices(self) -> list[str]:
        """Get browseable root directories.

        Returns:
            List of available roots with emoji prefixes
        """
        choices = ["📁 outputs"]
        if self.catalog_dir:
            choices.append("📁 catalog")
        return choices

    def set_root(self, root_name: str) -> None:
        """Switch between outputs and catalog root.

        Args:
            root_name: Root name ("outputs" or "catalog", optionally with 📁 prefix)
        """
        # Strip emoji prefix if present
        root_name = root_name.replace("📁 ", "").strip()

        if root_name == "outputs":
            self.current_root = self.outputs_dir
            logger.info("Switched to outputs root")
        elif root_name == "catalog" and self.catalog_dir:
            self.current_root = self.catalog_dir
            logger.info("Switched to catalog root")
        else:
            logger.warning(f"Invalid root name: {root_name}")

    def get_current_root_name(self) -> str:
        """Get the current root directory name.

        Returns:
            "outputs" or "catalog"
        """
        if self.current_root == self.outputs_dir:
            return "outputs"
        elif self.current_root == self.catalog_dir:
            return "catalog"
        else:
            return "outputs"  # Default

    def validate_path(self, relative_path: str) -> bool:
        """Validate that a relative path stays within current root directory.

        This method provides security against path traversal attacks by ensuring
        that user-provided paths cannot escape the outputs/catalog directories.
        For example, paths like "../../../etc/passwd" are rejected.

        The validation works by:
        1. Resolving the path to its absolute form (follows symlinks)
        2. Checking if the resolved path is within the root directory tree
        3. Rejecting any path that escapes the root

        Args:
            relative_path: Path relative to current_root

        Returns:
            True if path is safe (within root), False otherwise

        Notes:
            - Empty paths are considered valid (refers to root itself)
            - Path resolution follows symbolic links
            - Uses Path.is_relative_to() for safe containment check
            - Catches both ValueError (invalid path) and OSError (permission issues)

        Examples:
            >>> browser = GalleryBrowser(Path("outputs"))
            >>> browser.validate_path("subfolder/image.png")  # OK
            True
            >>> browser.validate_path("../../../etc/passwd")  # Rejected
            False
        """
        if not relative_path:
            return True

        try:
            # Combine root with relative path and resolve to absolute form
            # .resolve() follows symlinks and normalizes the path
            full_path = (self.current_root / relative_path).resolve()

            # Check if resolved path is within the root directory tree
            # This prevents path traversal attacks (../ escaping)
            return full_path.is_relative_to(self.current_root.resolve())
        except (ValueError, OSError):
            # ValueError: malformed path
            # OSError: permission denied or path doesn't exist
            return False

    def get_items_in_path(self, relative_path: str = "") -> tuple[list[str], list[str]]:
        """
        Get folders and image files at a specific path level (non-recursive).

        Args:
            relative_path: Path relative to current_root (empty string for root)

        Returns:
            Tuple of (folders, image_files) at this level only
        """
        # Validate path
        if relative_path and not self.validate_path(relative_path):
            logger.error(f"Invalid path: {relative_path}")
            return [], []

        current_path = self.current_root / relative_path if relative_path else self.current_root

        if not current_path.exists():
            return [], []

        folders = []
        images = []

        try:
            # Iterate through items at this level only (not recursive)
            for item in sorted(current_path.iterdir()):
                if item.is_dir():
                    # Only add directory if it contains images (directly or in subdirectories)
                    # This avoids showing empty directories in the UI
                    # rglob("*.png") recursively searches for PNG files
                    # any() returns True if at least one PNG is found
                    if any(item.rglob("*.png")):
                        folders.append(item.name)
                elif item.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                    # Add image files at this level
                    images.append(item.name)
        except PermissionError:
            logger.error(f"Permission denied accessing: {current_path}")

        return folders, images

    def scan_images(self, relative_path: str = "") -> list[str]:
        """
        Scan for all images at a specific path level (non-recursive).

        Args:
            relative_path: Path relative to current_root

        Returns:
            List of full paths to image files
        """
        # Validate path
        if relative_path and not self.validate_path(relative_path):
            logger.error(f"Invalid path: {relative_path}")
            return []

        current_path = self.current_root / relative_path if relative_path else self.current_root

        if not current_path.exists():
            return []

        images = []
        try:
            # Only get images in current directory, not recursive
            for item in sorted(current_path.iterdir()):
                if item.is_file() and item.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                    images.append(str(item))
        except PermissionError:
            logger.error(f"Permission denied accessing: {current_path}")

        return images

    def read_txt_metadata(self, image_path: str) -> str | None:
        """
        Read .txt metadata file for an image.

        Args:
            image_path: Full path to image file

        Returns:
            Text content (prompt) or None if not found
        """
        image_path_obj = Path(image_path)
        txt_path = image_path_obj.with_suffix(".txt")

        if not txt_path.exists():
            return None

        try:
            with open(txt_path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading {txt_path}: {e}")
            return None

    def read_json_metadata(self, image_path: str) -> dict[str, Any] | None:
        """
        Read .json metadata file for an image.

        Args:
            image_path: Full path to image file

        Returns:
            Parsed JSON dictionary or None if not found
        """
        image_path_obj = Path(image_path)
        json_path = image_path_obj.with_suffix(".json")

        if not json_path.exists():
            return None

        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                return None
        except Exception as e:
            logger.error(f"Error reading {json_path}: {e}")
            return None

    def format_metadata_txt(self, txt_content: str | None, image_name: str) -> str:
        """
        Format .txt metadata as Markdown for display.

        Args:
            txt_content: Text content (prompt) or None
            image_name: Name of the image file

        Returns:
            Formatted Markdown string
        """
        if txt_content is None:
            return f"**{image_name}**\n\n*No .txt metadata found*"

        return f"**{image_name}**\n\n**Prompt:**\n\n{txt_content}"

    def format_metadata_json(self, json_data: dict[str, Any] | None, image_name: str) -> str:
        """
        Format .json metadata as Markdown table for display.

        Args:
            json_data: Parsed JSON dictionary or None
            image_name: Name of the image file

        Returns:
            Formatted Markdown string
        """
        if json_data is None:
            return f"**{image_name}**\n\n*No .json metadata found*"

        # Build markdown table
        markdown = f"**{image_name}**\n\n"
        markdown += "| Parameter | Value |\n"
        markdown += "|-----------|-------|\n"

        # Key fields in order
        key_fields = [
            "prompt",
            "width",
            "height",
            "num_inference_steps",
            "seed",
            "guidance_scale",
            "model_id",
            "timestamp",
        ]

        for key in key_fields:
            if key in json_data:
                value = json_data[key]
                # Truncate long prompts
                if key == "prompt" and isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                markdown += f"| {key} | {value} |\n"

        # Add any additional fields
        for key, value in json_data.items():
            if key not in key_fields:
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                markdown += f"| {key} | {value} |\n"

        return markdown

    def get_image_count(self, relative_path: str = "") -> int:
        """
        Get count of images at a specific path level.

        Args:
            relative_path: Path relative to outputs_dir

        Returns:
            Number of images found
        """
        return len(self.scan_images(relative_path))
