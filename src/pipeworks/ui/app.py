"""Gradio UI for Pipeworks Image Generator with workflow and plugin support."""

import logging
import random
from pathlib import Path
from typing import Dict

import gradio as gr

from pipeworks.core.config import config
from pipeworks.core.pipeline import ImageGenerator
from pipeworks.plugins import SaveMetadataPlugin, plugin_registry
from pipeworks.workflows import workflow_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize generator
generator = ImageGenerator(config)

# Initialize workflows with the generator
workflows = {}
for workflow_name in workflow_registry.list_available():
    workflows[workflow_name] = workflow_registry.instantiate(workflow_name, generator=generator)

# Initialize plugins (disabled by default, will be enabled via UI)
available_plugins = {
    "SaveMetadata": SaveMetadataPlugin(folder_name="metadata", filename_prefix=""),
}

# Current active plugins list
active_plugins = []


def update_active_plugins(
    save_metadata_enabled: bool,
    metadata_folder: str,
    metadata_prefix: str,
) -> str:
    """Update the list of active plugins based on UI settings."""
    global active_plugins
    active_plugins = []

    if save_metadata_enabled:
        metadata_plugin = SaveMetadataPlugin(
            folder_name=metadata_folder if metadata_folder else None,
            filename_prefix=metadata_prefix if metadata_prefix else "",
        )
        active_plugins.append(metadata_plugin)

    # Update generator's plugins
    generator.plugins = active_plugins

    enabled_names = [p.name for p in active_plugins]
    return f"Active plugins: {', '.join(enabled_names) if enabled_names else 'None'}"


def generate_with_workflow(
    workflow_name: str,
    # Common parameters
    width: int,
    height: int,
    num_steps: int,
    seed: int,
    use_random_seed: bool,
    # Character workflow params
    character_type: str = "",
    character_mood: str = "",
    character_style: str = "photorealistic",
    character_clothing: str = "",
    character_background: str = "simple background",
    character_details: str = "",
    # GameAsset workflow params
    asset_item_name: str = "",
    asset_type: str = "container",
    asset_style: str = "isometric",
    asset_rarity: str = "",
    asset_material: str = "",
    asset_background: str = "plain background, no distractions",
    asset_details: str = "",
    # CityMap workflow params
    map_location_type: str = "city",
    map_style: str = "fantasy map",
    map_setting: str = "medieval",
    map_terrain: str = "",
    map_features: str = "",
    map_details: str = "",
) -> tuple[str, str, str]:
    """
    Generate an image using the selected workflow.

    Returns:
        Tuple of (image_path, info_text, seed_used)
    """
    try:
        # Get the workflow
        workflow = workflows.get(workflow_name)
        if not workflow:
            return None, f"Error: Workflow '{workflow_name}' not found", str(seed)

        # Generate random seed if requested
        actual_seed = random.randint(0, 2**32 - 1) if use_random_seed else seed

        # Build workflow-specific kwargs
        workflow_kwargs = {
            "width": width,
            "height": height,
            "num_inference_steps": num_steps,
            "seed": actual_seed,
        }

        # Add workflow-specific parameters
        if workflow_name == "Character":
            workflow_kwargs.update({
                "character_type": character_type,
                "mood": character_mood,
                "style": character_style,
                "clothing": character_clothing,
                "background": character_background,
                "additional_details": character_details,
            })
        elif workflow_name == "GameAsset":
            workflow_kwargs.update({
                "item_name": asset_item_name,
                "asset_type": asset_type,
                "style": asset_style,
                "rarity": asset_rarity,
                "material": asset_material,
                "background": asset_background,
                "additional_details": asset_details,
            })
        elif workflow_name == "CityMap":
            workflow_kwargs.update({
                "location_type": map_location_type,
                "map_style": map_style,
                "setting": map_setting,
                "terrain": map_terrain,
                "features": map_features,
                "additional_details": map_details,
            })

        # Generate image using workflow
        image, params = workflow.generate(**workflow_kwargs)

        # Save the image
        timestamp = Path(str(generator.config.outputs_dir)).name
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        seed_suffix = f"_seed{actual_seed}"
        filename = f"pipeworks_{workflow_name.lower()}_{timestamp}{seed_suffix}.png"
        save_path = generator.config.outputs_dir / filename
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Call plugin hooks for saving
        for plugin in active_plugins:
            if plugin.enabled:
                result = plugin.on_before_save(image, save_path, params)
                if result:
                    image, save_path = result

        image.save(save_path)
        logger.info(f"Image saved to: {save_path}")

        # Call after_save hooks
        for plugin in active_plugins:
            if plugin.enabled:
                plugin.on_after_save(image, save_path, params)

        # Create info text
        info = f"""
**Generation Complete!**

**Workflow:** {workflow_name}
**Prompt:** {params.get('prompt', 'N/A')}
**Dimensions:** {width}x{height}
**Steps:** {num_steps}
**Seed:** {actual_seed}
**Saved to:** {save_path}
**Active Plugins:** {', '.join([p.name for p in active_plugins]) if active_plugins else 'None'}
        """

        return str(save_path), info.strip(), str(actual_seed)

    except Exception as e:
        logger.error(f"Error generating image: {e}", exc_info=True)
        return None, f"Error: {str(e)}", str(seed)


def create_ui() -> gr.Blocks:
    """Create the Gradio UI."""

    with gr.Blocks(
        title="Pipeworks Image Generator",
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown(
            """
            # Pipeworks Image Generator
            ### Programmatic image generation with workflows and plugins
            """
        )

        with gr.Row():
            # Left column: Settings
            with gr.Column(scale=1):
                gr.Markdown("### Workflow Selection")

                workflow_selector = gr.Dropdown(
                    choices=list(workflows.keys()),
                    value=list(workflows.keys())[0] if workflows else None,
                    label="Workflow",
                    info="Select the generation workflow",
                )

                gr.Markdown("### Common Settings")

                with gr.Row():
                    width_slider = gr.Slider(
                        minimum=512,
                        maximum=2048,
                        step=64,
                        value=config.default_width,
                        label="Width",
                    )
                    height_slider = gr.Slider(
                        minimum=512,
                        maximum=2048,
                        step=64,
                        value=config.default_height,
                        label="Height",
                    )

                steps_slider = gr.Slider(
                    minimum=1,
                    maximum=20,
                    step=1,
                    value=config.num_inference_steps,
                    label="Inference Steps",
                )

                with gr.Row():
                    seed_input = gr.Number(
                        label="Seed",
                        value=42,
                        precision=0,
                    )
                    random_seed_checkbox = gr.Checkbox(
                        label="Random Seed",
                        value=False,
                    )

                # Character Workflow Controls
                with gr.Group(visible=True) as character_controls:
                    gr.Markdown("#### Character Settings")
                    char_type = gr.Textbox(label="Character Type", value="young woman")
                    char_mood = gr.Textbox(label="Mood/Expression", value="")
                    char_style = gr.Dropdown(
                        choices=["photorealistic", "fantasy art", "anime", "oil painting", "digital art", "pixel art"],
                        value="photorealistic",
                        label="Art Style",
                    )
                    char_clothing = gr.Textbox(label="Clothing", value="")
                    char_background = gr.Textbox(label="Background", value="simple background")
                    char_details = gr.Textbox(label="Additional Details", value="")

                # GameAsset Workflow Controls
                with gr.Group(visible=False) as gameasset_controls:
                    gr.Markdown("#### Game Asset Settings")
                    asset_name = gr.Textbox(label="Item Name", value="ink bottle")
                    asset_type_dd = gr.Dropdown(
                        choices=["weapon", "potion", "armor", "tool", "consumable", "artifact", "container", "misc"],
                        value="container",
                        label="Asset Type",
                    )
                    asset_style_dd = gr.Dropdown(
                        choices=["isometric", "pixel art", "hand-drawn", "3D render", "photorealistic"],
                        value="isometric",
                        label="Visual Style",
                    )
                    asset_rarity_dd = gr.Dropdown(
                        choices=["", "common", "uncommon", "rare", "epic", "legendary"],
                        value="",
                        label="Rarity",
                    )
                    asset_material_txt = gr.Textbox(label="Material", value="")
                    asset_background_txt = gr.Textbox(label="Background", value="plain background, no distractions")
                    asset_details_txt = gr.Textbox(label="Additional Details", value="")

                # CityMap Workflow Controls
                with gr.Group(visible=False) as citymap_controls:
                    gr.Markdown("#### City Map Settings")
                    map_location = gr.Dropdown(
                        choices=["city", "town", "village", "fortress", "dungeon", "region", "continent"],
                        value="city",
                        label="Location Type",
                    )
                    map_style_dd = gr.Dropdown(
                        choices=["fantasy map", "blueprint", "satellite view", "tactical map", "isometric view"],
                        value="fantasy map",
                        label="Map Style",
                    )
                    map_setting_dd = gr.Dropdown(
                        choices=["medieval", "ancient", "modern", "sci-fi", "post-apocalyptic", "steampunk"],
                        value="medieval",
                        label="Setting",
                    )
                    map_terrain_txt = gr.Textbox(label="Terrain", value="")
                    map_features_txt = gr.Textbox(label="Notable Features", value="")
                    map_details_txt = gr.Textbox(label="Additional Details", value="")

                # Plugin Management
                gr.Markdown("### Plugins")
                with gr.Accordion("Plugin Settings", open=False):
                    save_metadata_check = gr.Checkbox(
                        label="Save Metadata (.txt + .json)",
                        value=False,
                    )
                    metadata_folder_txt = gr.Textbox(
                        label="Metadata Folder",
                        value="metadata",
                        info="Subfolder within outputs directory",
                    )
                    metadata_prefix_txt = gr.Textbox(
                        label="Filename Prefix",
                        value="",
                        info="Prefix for metadata files",
                    )
                    plugin_status = gr.Textbox(
                        label="Plugin Status",
                        value="Active plugins: None",
                        interactive=False,
                    )
                    update_plugins_btn = gr.Button("Update Plugins", size="sm")

                generate_btn = gr.Button(
                    "Generate Image",
                    variant="primary",
                    size="lg",
                )

                info_output = gr.Markdown(
                    value="*Ready to generate images*",
                )

            # Right column: Output
            with gr.Column(scale=1):
                gr.Markdown("### Generated Image")

                image_output = gr.Image(
                    label="Output",
                    type="filepath",
                    height=600,
                )

                seed_used = gr.Textbox(
                    label="Seed Used",
                    interactive=False,
                    value="42",
                )

        # Model info footer
        gr.Markdown(
            f"""
            ---
            **Model:** {config.model_id} | **Device:** {config.device} | **Dtype:** {config.torch_dtype}

            *Outputs saved to: {config.outputs_dir}*
            """
        )

        # Workflow selector logic - show/hide relevant controls
        def update_workflow_ui(workflow_name):
            return {
                character_controls: gr.update(visible=(workflow_name == "Character")),
                gameasset_controls: gr.update(visible=(workflow_name == "GameAsset")),
                citymap_controls: gr.update(visible=(workflow_name == "CityMap")),
            }

        workflow_selector.change(
            fn=update_workflow_ui,
            inputs=[workflow_selector],
            outputs=[character_controls, gameasset_controls, citymap_controls],
        )

        # Plugin update handler
        update_plugins_btn.click(
            fn=update_active_plugins,
            inputs=[save_metadata_check, metadata_folder_txt, metadata_prefix_txt],
            outputs=[plugin_status],
        )

        # Generation handler
        generate_btn.click(
            fn=generate_with_workflow,
            inputs=[
                workflow_selector,
                width_slider,
                height_slider,
                steps_slider,
                seed_input,
                random_seed_checkbox,
                # Character
                char_type, char_mood, char_style, char_clothing, char_background, char_details,
                # GameAsset
                asset_name, asset_type_dd, asset_style_dd, asset_rarity_dd, asset_material_txt,
                asset_background_txt, asset_details_txt,
                # CityMap
                map_location, map_style_dd, map_setting_dd, map_terrain_txt, map_features_txt, map_details_txt,
            ],
            outputs=[image_output, info_output, seed_used],
        )

    return app


def main():
    """Main entry point for the application."""
    logger.info("Starting Pipeworks Image Generator...")
    logger.info(f"Configuration: {config.model_dump()}")

    # Pre-load model on startup
    logger.info("Pre-loading model...")
    try:
        generator.load_model()
    except Exception as e:
        logger.error(f"Failed to pre-load model: {e}")
        logger.warning("Model will be loaded on first generation attempt")

    # Create and launch UI
    app = create_ui()

    logger.info(
        f"Launching Gradio UI on {config.gradio_server_name}:{config.gradio_server_port}"
    )

    app.launch(
        server_name=config.gradio_server_name,
        server_port=config.gradio_server_port,
        share=config.gradio_share,
        show_error=True,
    )


if __name__ == "__main__":
    main()
