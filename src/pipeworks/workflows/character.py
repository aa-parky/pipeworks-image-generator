"""Character generation workflow for portraits and character art."""

import logging

from pipeworks.workflows.base import WorkflowBase, workflow_registry

logger = logging.getLogger(__name__)


class CharacterWorkflow(WorkflowBase):
    """
    Workflow for generating character portraits and character art.

    Optimized for:
    - Portrait framing
    - Character details and expressions
    - Consistent character design
    """

    name = "Character"
    description = "Generate character portraits and character art"
    version = "0.1.0"

    # Character-specific defaults
    default_width = 1024
    default_height = 1024
    default_steps = 9
    default_guidance_scale = 0.0

    def build_prompt(
        self,
        character_type: str = "",
        mood: str = "",
        style: str = "photorealistic",
        clothing: str = "",
        background: str = "simple background",
        additional_details: str = "",
        **kwargs,
    ) -> str:
        """
        Build character generation prompt.

        Args:
            character_type: Type of character (e.g., "young woman", "dwarf warrior")
            mood: Character mood/expression (e.g., "confident", "mysterious")
            style: Art style (e.g., "photorealistic", "fantasy art", "anime")
            clothing: Character clothing/outfit description
            background: Background description
            additional_details: Any additional prompt details

        Returns:
            Formatted prompt
        """
        prompt_parts = []

        # Character type (required)
        if character_type:
            prompt_parts.append(character_type)

        # Mood/expression
        if mood:
            prompt_parts.append(f"{mood} expression")

        # Clothing
        if clothing:
            prompt_parts.append(f"wearing {clothing}")

        # Background
        if background:
            prompt_parts.append(background)

        # Style directive
        prompt_parts.append(style)

        # Additional details
        if additional_details:
            prompt_parts.append(additional_details)

        # Add quality boosters for character work
        prompt_parts.append("high detail, sharp focus, professional lighting")

        prompt = ", ".join(prompt_parts)
        return prompt

    def get_ui_controls(self):
        """Define UI controls specific to character generation."""
        return {
            "character_type": {
                "type": "text",
                "label": "Character Type",
                "placeholder": "e.g., young woman, dwarf warrior, elf mage",
                "value": "young woman",
            },
            "mood": {
                "type": "text",
                "label": "Mood/Expression",
                "placeholder": "e.g., confident, mysterious, cheerful",
                "value": "",
            },
            "style": {
                "type": "dropdown",
                "label": "Art Style",
                "choices": [
                    "photorealistic",
                    "fantasy art",
                    "anime",
                    "oil painting",
                    "digital art",
                    "pixel art",
                ],
                "value": "photorealistic",
            },
            "clothing": {
                "type": "text",
                "label": "Clothing/Outfit",
                "placeholder": "e.g., red traditional dress, leather armor",
                "value": "",
            },
            "background": {
                "type": "text",
                "label": "Background",
                "value": "simple background",
            },
            "additional_details": {
                "type": "text",
                "label": "Additional Details",
                "placeholder": "Any other details to add to the prompt",
                "value": "",
            },
        }


# Register the workflow
workflow_registry.register(CharacterWorkflow)
