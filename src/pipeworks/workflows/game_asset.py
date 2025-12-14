"""Game asset generation workflow for items, props, and objects."""

import logging

from pipeworks.workflows.base import WorkflowBase, workflow_registry

logger = logging.getLogger(__name__)


class GameAssetWorkflow(WorkflowBase):
    """
    Workflow for generating game assets (items, props, objects).

    Optimized for:
    - Isometric or specific projection views
    - Clean, isolated objects
    - Consistent asset style
    - Item readability
    """

    name = "GameAsset"
    description = "Generate game assets like items, props, and objects"
    version = "0.1.0"

    # Game asset defaults
    default_width = 1024
    default_height = 1024
    default_steps = 9
    default_guidance_scale = 0.0

    def build_prompt(
        self,
        asset_type: str = "",
        item_name: str = "",
        style: str = "isometric",
        material: str = "",
        rarity: str = "",
        background: str = "plain background, no distractions",
        additional_details: str = "",
        **kwargs,
    ) -> str:
        """
        Build game asset generation prompt.

        Args:
            asset_type: Type of asset (e.g., "weapon", "potion", "armor", "tool")
            item_name: Specific item name (e.g., "health potion", "iron sword")
            style: Visual style (e.g., "isometric", "pixel art", "hand-drawn")
            material: Material description (e.g., "glass", "metal", "wood")
            rarity: Item rarity tier (e.g., "common", "rare", "legendary")
            background: Background description
            additional_details: Additional prompt details

        Returns:
            Formatted prompt
        """
        prompt_parts = []

        # Rarity prefix (for visual flair)
        if rarity:
            prompt_parts.append(rarity)

        # Asset type and name
        if asset_type and item_name:
            prompt_parts.append(f"{asset_type}: {item_name}")
        elif item_name:
            prompt_parts.append(item_name)
        elif asset_type:
            prompt_parts.append(asset_type)

        # Material
        if material:
            prompt_parts.append(f"{material} material")

        # Background
        if background:
            prompt_parts.append(background)

        # Style directive
        if style == "isometric":
            prompt_parts.append("isometric projection, a small dark bottle with a cork")
        elif style == "pixel art":
            prompt_parts.append("pixel art style, clean pixels, game sprite")
        elif style == "hand-drawn":
            prompt_parts.append("hand-drawn, sketch on aged parchment")
        else:
            prompt_parts.append(style)

        # Additional details
        if additional_details:
            prompt_parts.append(additional_details)

        # Quality boosters for asset work
        prompt_parts.append(
            "in the style of a detailed ink and pencil fantasy sketch on aged parchment paper"
        )

        prompt = ", ".join(prompt_parts)
        return prompt

    def get_ui_controls(self):
        """Define UI controls specific to game asset generation."""
        return {
            "item_name": {
                "type": "text",
                "label": "Item Name",
                "placeholder": "e.g., health potion, iron sword, magic scroll",
                "value": "ink bottle",
            },
            "asset_type": {
                "type": "dropdown",
                "label": "Asset Type",
                "choices": [
                    "weapon",
                    "potion",
                    "armor",
                    "tool",
                    "consumable",
                    "artifact",
                    "container",
                    "misc",
                ],
                "value": "container",
            },
            "style": {
                "type": "dropdown",
                "label": "Visual Style",
                "choices": [
                    "isometric",
                    "pixel art",
                    "hand-drawn",
                    "3D render",
                    "photorealistic",
                ],
                "value": "isometric",
            },
            "rarity": {
                "type": "dropdown",
                "label": "Rarity",
                "choices": ["", "common", "uncommon", "rare", "epic", "legendary"],
                "value": "",
            },
            "material": {
                "type": "text",
                "label": "Material",
                "placeholder": "e.g., glass, metal, wood, crystal",
                "value": "",
            },
            "background": {
                "type": "text",
                "label": "Background",
                "value": "plain background, no distractions",
            },
            "additional_details": {
                "type": "text",
                "label": "Additional Details",
                "placeholder": "Any other details to add",
                "value": "",
            },
        }


# Register the workflow
workflow_registry.register(GameAssetWorkflow)
