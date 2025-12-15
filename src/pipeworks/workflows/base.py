"""Base classes and registry for the Pipeworks workflow system."""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class WorkflowBase(ABC):
    """
    Base class for all Pipeworks workflows.

    Workflows encapsulate generation strategies for specific content types.
    Each workflow defines:
    - Prompt engineering approach
    - Default parameters
    - Pre/post processing logic
    - UI controls specific to the workflow
    """

    name: str = "Base Workflow"
    description: str = "Base workflow class"
    version: str = "0.1.0"

    # Default generation parameters (can be overridden by subclasses)
    default_width: int = 1024
    default_height: int = 1024
    default_steps: int = 9
    default_guidance_scale: float = 0.0

    def __init__(self, generator=None):
        """
        Initialize the workflow.

        Args:
            generator: ImageGenerator instance to use for generation
        """
        self.generator = generator
        logger.info(f"Initialized workflow: {self.name}")

    @abstractmethod
    def build_prompt(self, **kwargs) -> str:
        """
        Build the generation prompt based on workflow-specific parameters.

        Args:
            **kwargs: Workflow-specific parameters

        Returns:
            Formatted prompt string
        """
        pass

    def get_generation_params(self, **kwargs) -> dict[str, Any]:
        """
        Get generation parameters for this workflow.

        Args:
            **kwargs: User-provided parameters

        Returns:
            Dictionary of generation parameters
        """
        return {
            "width": kwargs.get("width", self.default_width),
            "height": kwargs.get("height", self.default_height),
            "num_inference_steps": kwargs.get("num_inference_steps", self.default_steps),
            "guidance_scale": kwargs.get("guidance_scale", self.default_guidance_scale),
            "seed": kwargs.get("seed"),
        }

    def preprocess(self, **kwargs) -> dict[str, Any]:
        """
        Preprocess inputs before generation (optional override).

        Args:
            **kwargs: Workflow inputs

        Returns:
            Processed inputs
        """
        return kwargs

    def postprocess(self, image, **kwargs):
        """
        Postprocess the generated image (optional override).

        Args:
            image: Generated image
            **kwargs: Additional parameters

        Returns:
            Processed image
        """
        return image

    def generate(self, **kwargs):
        """
        Main generation method that orchestrates the workflow.

        Args:
            **kwargs: Workflow-specific parameters

        Returns:
            Generated and processed image
        """
        if self.generator is None:
            raise RuntimeError("No generator instance attached to workflow")

        # Preprocess inputs
        inputs = self.preprocess(**kwargs)

        # Build prompt
        prompt = self.build_prompt(**inputs)
        logger.info(f"[{self.name}] Generated prompt: {prompt}")

        # Get generation parameters
        params = self.get_generation_params(**inputs)
        params["prompt"] = prompt

        # Generate image
        image = self.generator.generate(**params)

        # Postprocess
        image = self.postprocess(image, **inputs)

        return image, params

    def get_ui_controls(self) -> dict[str, Any]:
        """
        Define workflow-specific UI controls for Gradio.

        Returns:
            Dictionary of control definitions
        """
        return {}


class WorkflowRegistry:
    """Registry for managing available workflows."""

    def __init__(self):
        self._workflows: dict[str, type[WorkflowBase]] = {}
        self._instances: dict[str, WorkflowBase] = {}

    def register(self, workflow_class: type[WorkflowBase]) -> None:
        """
        Register a workflow class.

        Args:
            workflow_class: Workflow class to register
        """
        workflow_name = workflow_class.name
        self._workflows[workflow_name] = workflow_class
        logger.info(f"Registered workflow: {workflow_name}")

    def instantiate(self, workflow_name: str, generator=None) -> WorkflowBase | None:
        """
        Create an instance of a registered workflow.

        Args:
            workflow_name: Name of the workflow to instantiate
            generator: ImageGenerator instance

        Returns:
            Workflow instance or None if not found
        """
        if workflow_name not in self._workflows:
            logger.error(f"Workflow not found: {workflow_name}")
            return None

        instance = self._workflows[workflow_name](generator=generator)
        self._instances[workflow_name] = instance
        return instance

    def get_instance(self, workflow_name: str) -> WorkflowBase | None:
        """Get an existing workflow instance."""
        return self._instances.get(workflow_name)

    def list_available(self) -> list[str]:
        """List all registered workflow names."""
        return list(self._workflows.keys())

    def get_workflow_info(self, workflow_name: str) -> dict[str, str] | None:
        """Get information about a workflow."""
        if workflow_name not in self._workflows:
            return None

        workflow_class = self._workflows[workflow_name]
        return {
            "name": workflow_class.name,
            "description": workflow_class.description,
            "version": workflow_class.version,
        }


# Global workflow registry
workflow_registry = WorkflowRegistry()
