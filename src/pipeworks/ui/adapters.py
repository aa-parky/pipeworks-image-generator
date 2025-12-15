"""Adapter functions for converting between UI values and business objects."""

from .components import SegmentUI
from .models import SegmentConfig


def convert_segment_values_to_configs(
    start_values: tuple,
    middle_values: tuple,
    end_values: tuple,
) -> tuple[SegmentConfig, SegmentConfig, SegmentConfig]:
    """Convert raw UI segment values to SegmentConfig objects.

    Args:
        start_values: 8-tuple of start segment values
        middle_values: 8-tuple of middle segment values
        end_values: 8-tuple of end segment values

    Returns:
        Tuple of (start_cfg, middle_cfg, end_cfg)
    """
    return (
        SegmentUI.values_to_config(*start_values),
        SegmentUI.values_to_config(*middle_values),
        SegmentUI.values_to_config(*end_values),
    )


def split_segment_inputs(values: list) -> tuple[tuple, tuple, tuple, any]:
    """Split combined input list into segment groups.

    Args:
        values: List of all UI input values

    Returns:
        Tuple of (start_values, middle_values, end_values, state)
        Each segment values is an 8-tuple
    """
    start_values = tuple(values[0:8])
    middle_values = tuple(values[8:16])
    end_values = tuple(values[16:24])
    state = values[24]
    return start_values, middle_values, end_values, state
