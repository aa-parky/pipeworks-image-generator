"""City map generation workflow for overhead views and map layouts."""

import logging

from pipeworks.workflows.base import WorkflowBase, workflow_registry

logger = logging.getLogger(__name__)


class CityMapWorkflow(WorkflowBase):
    """
    Workflow for generating city maps and overhead views.

    Optimized for:
    - Top-down/overhead perspective
    - Architectural layouts
    - Map-style rendering
    - Strategic/planning views
    """

    name = "CityMap"
    description = "Generate city maps and overhead architectural views"
    version = "0.1.0"

    # City map defaults
    default_width = 1024
    default_height = 1024
    default_steps = 9
    default_guidance_scale = 0.0

    def build_prompt(
        self,
        location_type: str = "city",
        map_style: str = "fantasy map",
        setting: str = "medieval",
        features: str = "",
        terrain: str = "",
        additional_details: str = "",
        **kwargs,
    ) -> str:
        """
        Build city map generation prompt.

        Args:
            location_type: Type of location (e.g., "city", "town", "village", "dungeon")
            map_style: Style of map (e.g., "fantasy map", "blueprint", "satellite view")
            setting: Time period/setting (e.g., "medieval", "modern", "sci-fi")
            features: Notable features (e.g., "castle, marketplace, river")
            terrain: Terrain description (e.g., "coastal", "mountain valley")
            additional_details: Additional prompt details

        Returns:
            Formatted prompt
        """
        prompt_parts = []

        # Map perspective
        prompt_parts.append("overhead view")

        # Setting and location type
        if setting:
            prompt_parts.append(f"{setting} {location_type}")
        else:
            prompt_parts.append(location_type)

        # Terrain
        if terrain:
            prompt_parts.append(f"{terrain} terrain")

        # Features
        if features:
            prompt_parts.append(f"featuring {features}")

        # Map style directive
        if map_style == "fantasy map":
            prompt_parts.append("fantasy map style, hand-drawn, parchment, cartographic details")
        elif map_style == "blueprint":
            prompt_parts.append("architectural blueprint, technical drawing, clean lines")
        elif map_style == "satellite view":
            prompt_parts.append("satellite view, photorealistic, aerial perspective")
        elif map_style == "tactical map":
            prompt_parts.append("tactical map, grid overlay, strategic markers")
        else:
            prompt_parts.append(map_style)

        # Additional details
        if additional_details:
            prompt_parts.append(additional_details)

        # Quality boosters for map work
        prompt_parts.append("detailed, clear layout, high contrast")

        prompt = ", ".join(prompt_parts)
        return prompt

    def get_ui_controls(self):
        """Define UI controls specific to city map generation."""
        return {
            "location_type": {
                "type": "dropdown",
                "label": "Location Type",
                "choices": [
                    "city",
                    "town",
                    "village",
                    "fortress",
                    "dungeon",
                    "region",
                    "continent",
                ],
                "value": "city",
            },
            "map_style": {
                "type": "dropdown",
                "label": "Map Style",
                "choices": [
                    "fantasy map",
                    "blueprint",
                    "satellite view",
                    "tactical map",
                    "isometric view",
                ],
                "value": "fantasy map",
            },
            "setting": {
                "type": "dropdown",
                "label": "Setting",
                "choices": [
                    "medieval",
                    "ancient",
                    "modern",
                    "sci-fi",
                    "post-apocalyptic",
                    "steampunk",
                ],
                "value": "medieval",
            },
            "terrain": {
                "type": "text",
                "label": "Terrain",
                "placeholder": "e.g., coastal, mountain valley, desert oasis",
                "value": "",
            },
            "features": {
                "type": "text",
                "label": "Notable Features",
                "placeholder": "e.g., castle, marketplace, river, city walls",
                "value": "",
            },
            "additional_details": {
                "type": "text",
                "label": "Additional Details",
                "placeholder": "Any other details to add",
                "value": "",
            },
        }


# Register the workflow
workflow_registry.register(CityMapWorkflow)
