"""Workflow orchestration for complex image generation pipelines.

Workflows encapsulate generation strategies for specific content types:
- CharacterWorkflow: Character portraits and character art
- GameAssetWorkflow: Game items, props, and objects
- CityMapWorkflow: Overhead city maps and architectural views

Each workflow provides:
- Specialized prompt engineering
- Content-type specific parameters
- Custom UI controls
- Pre/post processing logic
"""

from pipeworks.workflows.base import WorkflowBase, WorkflowRegistry, workflow_registry
from pipeworks.workflows.character import CharacterWorkflow
from pipeworks.workflows.city_map import CityMapWorkflow
from pipeworks.workflows.game_asset import GameAssetWorkflow

__all__ = [
    "WorkflowBase",
    "WorkflowRegistry",
    "workflow_registry",
    "CharacterWorkflow",
    "GameAssetWorkflow",
    "CityMapWorkflow",
]
