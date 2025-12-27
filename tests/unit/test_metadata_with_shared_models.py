"""Tests for metadata saving with shared model architecture.

This module tests that the SaveMetadataPlugin correctly saves prompts
and metadata even with the class-level shared model pattern introduced
to fix browser refresh OOM issues.
"""

import json
from unittest.mock import patch

import pytest

from pipeworks.core.adapters.zimage_turbo import ZImageTurboAdapter
from pipeworks.core.config import PipeworksConfig
from pipeworks.plugins.save_metadata import SaveMetadataPlugin


# Mock class from test_model_adapters.py
class MockZImagePipeline:
    """Mock for ZImagePipeline."""

    def __init__(self, *args, **kwargs):
        """Initialize the mock pipeline."""
        from unittest.mock import MagicMock

        self.transformer = MagicMock()
        self.device = None
        self._called_with = {}

    def to(self, device):
        """Mock the to() method."""
        self.device = device
        return self

    def enable_model_cpu_offload(self):
        """Mock CPU offload enabling."""
        self._called_with["cpu_offload"] = True

    def enable_attention_slicing(self):
        """Mock attention slicing enabling."""
        self._called_with["attention_slicing"] = True

    def __call__(self, prompt, height, width, num_inference_steps, guidance_scale, generator=None):
        """Mock the pipeline call."""
        from unittest.mock import MagicMock

        from PIL import Image

        # Store call parameters
        self._called_with.update(
            {
                "prompt": prompt,
                "height": height,
                "width": width,
                "steps": num_inference_steps,
                "guidance": guidance_scale,
                "generator": generator,
            }
        )

        # Return mock output
        mock_output = MagicMock()
        mock_output.images = [Image.new("RGB", (width, height))]
        return mock_output


@pytest.fixture(autouse=True)
def cleanup_shared_state():
    """Clean up class-level shared state before and after each test."""
    # Clean up before test
    ZImageTurboAdapter._shared_pipe = None
    ZImageTurboAdapter._shared_model_id = None
    ZImageTurboAdapter._instance_count = 0

    yield

    # Clean up after test
    ZImageTurboAdapter._shared_pipe = None
    ZImageTurboAdapter._shared_model_id = None
    ZImageTurboAdapter._instance_count = 0


@pytest.fixture
def test_config(tmp_path):
    """Create test configuration."""
    return PipeworksConfig(
        device="cpu",
        torch_dtype="float32",
        zimage_model_id="mock/zimage-turbo",
        outputs_dir=tmp_path / "outputs",
        models_dir=tmp_path / "models",
        compile_model=False,
        enable_model_cpu_offload=False,
        enable_attention_slicing=False,
    )


@pytest.mark.unit
class TestMetadataWithSharedModels:
    """Test metadata saving with shared model architecture."""

    @patch("diffusers.ZImagePipeline")
    def test_metadata_saved_with_single_instance(self, mock_pipeline_class, test_config, tmp_path):
        """Test that metadata is saved correctly with a single adapter instance."""
        # Setup
        mock_pipeline_class.from_pretrained.return_value = MockZImagePipeline()
        test_config.outputs_dir.mkdir(parents=True, exist_ok=True)

        # Create adapter with SaveMetadata plugin
        metadata_plugin = SaveMetadataPlugin()
        metadata_plugin.enabled = True
        adapter = ZImageTurboAdapter(test_config, plugins=[metadata_plugin])

        # Load model
        adapter.load_model()

        # Generate and save with prompt
        test_prompt = "a beautiful sunset over mountains"
        image, save_path = adapter.generate_and_save(
            prompt=test_prompt,
            seed=42,
        )

        # Verify image was saved
        assert save_path.exists(), f"Image not saved at {save_path}"

        # Verify .txt metadata file was created
        txt_path = save_path.with_suffix(".txt")
        assert txt_path.exists(), f"Metadata .txt file not found at {txt_path}"

        # Verify prompt was saved correctly
        with open(txt_path, encoding="utf-8") as f:
            saved_prompt = f.read()
        assert saved_prompt == test_prompt, f"Expected '{test_prompt}', got '{saved_prompt}'"

        # Verify .json metadata file was created
        json_path = save_path.with_suffix(".json")
        assert json_path.exists(), f"Metadata .json file not found at {json_path}"

        # Verify JSON contains correct data
        with open(json_path, encoding="utf-8") as f:
            metadata = json.load(f)
        assert metadata["prompt"] == test_prompt
        assert metadata["seed"] == 42
        assert metadata["model_id"] == "mock/zimage-turbo"

    @patch("diffusers.ZImagePipeline")
    def test_metadata_saved_after_browser_refresh_simulation(
        self, mock_pipeline_class, test_config, tmp_path
    ):
        """Test that metadata is saved correctly after simulated browser refresh.

        This simulates what happens when a user refreshes their browser:
        1. First instance loads model and has plugins configured
        2. Browser refresh creates a new instance (with new plugin instance)
        3. New instance should still save metadata correctly

        This is the key test for the reported bug.
        """
        # Setup
        mock_pipeline_class.from_pretrained.return_value = MockZImagePipeline()
        test_config.outputs_dir.mkdir(parents=True, exist_ok=True)

        # FIRST SESSION: Create adapter with SaveMetadata plugin
        metadata_plugin_1 = SaveMetadataPlugin()
        metadata_plugin_1.enabled = True
        adapter_1 = ZImageTurboAdapter(test_config, plugins=[metadata_plugin_1])
        adapter_1.load_model()

        # Generate image in first session
        test_prompt_1 = "first session prompt"
        image_1, save_path_1 = adapter_1.generate_and_save(
            prompt=test_prompt_1,
            seed=111,
        )

        # Verify first session metadata
        txt_path_1 = save_path_1.with_suffix(".txt")
        assert txt_path_1.exists(), "First session: metadata not saved"
        with open(txt_path_1, encoding="utf-8") as f:
            assert f.read() == test_prompt_1, "First session: prompt incorrect"

        # BROWSER REFRESH: Create NEW adapter instance (simulating new session)
        # Key point: model is already loaded in class variable, but this is a new instance
        metadata_plugin_2 = SaveMetadataPlugin()
        metadata_plugin_2.enabled = True
        adapter_2 = ZImageTurboAdapter(test_config, plugins=[metadata_plugin_2])
        adapter_2.load_model()  # Should reuse existing model

        # Verify model was reused (not reloaded)
        assert ZImageTurboAdapter._instance_count == 2, "Should have 2 instances"
        assert adapter_1.is_loaded, "First adapter should report model as loaded"
        assert adapter_2.is_loaded, "Second adapter should report model as loaded"
        assert ZImageTurboAdapter._shared_pipe is not None, "Shared pipeline should be available"

        # Generate image in second session with NEW prompt
        test_prompt_2 = "second session prompt after browser refresh"
        image_2, save_path_2 = adapter_2.generate_and_save(
            prompt=test_prompt_2,
            seed=222,
        )

        # Verify second session metadata was saved (THIS IS THE BUG FIX TEST)
        txt_path_2 = save_path_2.with_suffix(".txt")
        assert txt_path_2.exists(), (
            "Second session: metadata .txt not saved "
            "(this is the bug - prompt not populating in gallery)"
        )

        with open(txt_path_2, encoding="utf-8") as f:
            saved_prompt_2 = f.read()
        assert saved_prompt_2 == test_prompt_2, (
            f"Second session: prompt incorrect. "
            f"Expected '{test_prompt_2}', got '{saved_prompt_2}'"
        )

        # Verify JSON was also saved
        json_path_2 = save_path_2.with_suffix(".json")
        assert json_path_2.exists(), "Second session: metadata .json not saved"
        with open(json_path_2, encoding="utf-8") as f:
            metadata_2 = json.load(f)
        assert metadata_2["prompt"] == test_prompt_2
        assert metadata_2["seed"] == 222

    @patch("diffusers.ZImagePipeline")
    def test_metadata_not_saved_when_plugin_disabled(
        self, mock_pipeline_class, test_config, tmp_path
    ):
        """Test that metadata is NOT saved when plugin is disabled."""
        # Setup
        mock_pipeline_class.from_pretrained.return_value = MockZImagePipeline()
        test_config.outputs_dir.mkdir(parents=True, exist_ok=True)

        # Create adapter with DISABLED plugin
        metadata_plugin = SaveMetadataPlugin()
        metadata_plugin.enabled = False  # Disabled
        adapter = ZImageTurboAdapter(test_config, plugins=[metadata_plugin])
        adapter.load_model()

        # Generate and save
        image, save_path = adapter.generate_and_save(
            prompt="test prompt",
            seed=42,
        )

        # Verify image was saved but metadata was NOT
        assert save_path.exists(), "Image should be saved"
        txt_path = save_path.with_suffix(".txt")
        assert not txt_path.exists(), "Metadata should NOT be saved when plugin is disabled"

    @patch("diffusers.ZImagePipeline")
    def test_metadata_not_saved_when_no_plugins(self, mock_pipeline_class, test_config, tmp_path):
        """Test that metadata is NOT saved when no plugins are configured."""
        # Setup
        mock_pipeline_class.from_pretrained.return_value = MockZImagePipeline()
        test_config.outputs_dir.mkdir(parents=True, exist_ok=True)

        # Create adapter with NO plugins (empty list)
        adapter = ZImageTurboAdapter(test_config, plugins=[])
        adapter.load_model()

        # Generate and save
        image, save_path = adapter.generate_and_save(
            prompt="test prompt",
            seed=42,
        )

        # Verify image was saved but metadata was NOT
        assert save_path.exists(), "Image should be saved"
        txt_path = save_path.with_suffix(".txt")
        assert not txt_path.exists(), "Metadata should NOT be saved when no plugins configured"
