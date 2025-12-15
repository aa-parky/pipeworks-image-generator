"""Gallery browser utility for viewing generated images and metadata."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class GalleryBrowser:
    """Browse generated images and their metadata in the outputs directory."""

    def __init__(self, outputs_dir: Path):
        """
        Initialize the gallery browser.

        Args:
            outputs_dir: Base directory containing generated images
        """
        self.outputs_dir = Path(outputs_dir)
        if not self.outputs_dir.exists():
            logger.warning(f"Outputs directory does not exist: {self.outputs_dir}")
            self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def validate_path(self, relative_path: str) -> bool:
        """
        Validate that a relative path stays within outputs directory.

        Args:
            relative_path: Path relative to outputs_dir

        Returns:
            True if path is safe, False otherwise
        """
        if not relative_path:
            return True

        try:
            full_path = (self.outputs_dir / relative_path).resolve()
            return full_path.is_relative_to(self.outputs_dir.resolve())
        except (ValueError, OSError):
            return False

    def get_items_in_path(self, relative_path: str = "") -> tuple[list[str], list[str]]:
        """
        Get folders and image files at a specific path level (non-recursive).

        Args:
            relative_path: Path relative to outputs_dir (empty string for root)

        Returns:
            Tuple of (folders, image_files) at this level only
        """
        # Validate path
        if relative_path and not self.validate_path(relative_path):
            logger.error(f"Invalid path: {relative_path}")
            return [], []

        current_path = self.outputs_dir / relative_path if relative_path else self.outputs_dir

        if not current_path.exists():
            return [], []

        folders = []
        images = []

        try:
            for item in sorted(current_path.iterdir()):
                if item.is_dir():
                    # Only add if directory contains images (directly or in subdirectories)
                    if any(item.rglob("*.png")):
                        folders.append(item.name)
                elif item.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                    images.append(item.name)
        except PermissionError:
            logger.error(f"Permission denied accessing: {current_path}")

        return folders, images

    def scan_images(self, relative_path: str = "") -> list[str]:
        """
        Scan for all images at a specific path level (non-recursive).

        Args:
            relative_path: Path relative to outputs_dir

        Returns:
            List of full paths to image files
        """
        # Validate path
        if relative_path and not self.validate_path(relative_path):
            logger.error(f"Invalid path: {relative_path}")
            return []

        current_path = self.outputs_dir / relative_path if relative_path else self.outputs_dir

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
        image_path = Path(image_path)
        txt_path = image_path.with_suffix(".txt")

        if not txt_path.exists():
            return None

        try:
            with open(txt_path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading {txt_path}: {e}")
            return None

    def read_json_metadata(self, image_path: str) -> dict | None:
        """
        Read .json metadata file for an image.

        Args:
            image_path: Full path to image file

        Returns:
            Parsed JSON dictionary or None if not found
        """
        image_path = Path(image_path)
        json_path = image_path.with_suffix(".json")

        if not json_path.exists():
            return None

        try:
            with open(json_path, encoding="utf-8") as f:
                return json.load(f)
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

    def format_metadata_json(self, json_data: dict | None, image_name: str) -> str:
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
