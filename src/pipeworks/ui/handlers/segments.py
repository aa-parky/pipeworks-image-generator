"""Segment management handlers for dynamic segment add/remove functionality.

This module provides handlers for managing dynamic segments in the prompt builder,
allowing users to add and remove segments as needed rather than being locked into
a fixed number of segments.
"""

import logging
from typing import Any

from ..models import UIState
from ..segment_plugins import SegmentUIComponents

logger = logging.getLogger(__name__)


def add_segment_handler(
    segment_manager_state: dict[str, Any],
    ui_state: UIState,
) -> tuple[dict[str, Any], str, UIState]:
    """Add a new segment to the segment manager.

    This handler creates a new segment and adds it to the segment manager state.
    It enforces the maximum segment limit and generates unique segment IDs.

    Args:
        segment_manager_state: Current segment manager state dict with keys:
            - segments: list of SegmentUIComponents
            - next_segment_id: int counter for unique IDs
            - max_segments: int maximum allowed segments
        ui_state: Current UI state

    Returns:
        Tuple of:
            - Updated segment_manager_state dict
            - Status message string
            - Updated ui_state

    Notes:
        - Enforces max_segments limit (default 10)
        - Generates unique segment IDs using counter
        - Returns error message if at max capacity
        - Segment creation must be done in UI context (not here)

    Examples:
        >>> state_dict = {"segments": [], "next_segment_id": 0, "max_segments": 10}
        >>> ui_state = UIState()
        >>> new_state, msg, ui_state = add_segment_handler(state_dict, ui_state)
        >>> print(msg)
        'Segment 0 added. Total: 1 segment(s).'
    """
    # Extract current state
    current_segments = segment_manager_state.get("segments", [])
    next_id = segment_manager_state.get("next_segment_id", 0)
    max_segments = segment_manager_state.get("max_segments", 10)

    # Check if at maximum capacity
    if len(current_segments) >= max_segments:
        logger.warning(f"Cannot add segment: at maximum capacity ({max_segments})")
        return (
            segment_manager_state,
            f"Maximum {max_segments} segments reached.",
            ui_state,
        )

    # Generate new segment ID
    new_segment_id = str(next_id)
    logger.info(f"Adding segment with ID: {new_segment_id}")

    # Note: Actual segment UI creation happens in the calling context
    # This handler just manages the state bookkeeping

    # Update state
    updated_state = {
        "segments": current_segments,  # Segment will be added by caller
        "next_segment_id": next_id + 1,  # Increment for next segment
        "max_segments": max_segments,
    }

    # Create status message
    new_count = len(current_segments) + 1
    message = f"Segment {new_segment_id} added. Total: {new_count} segment(s)."

    return updated_state, message, ui_state


def remove_segment_handler(
    segment_id: str,
    segment_manager_state: dict[str, Any],
    ui_state: UIState,
) -> tuple[dict[str, Any], str, UIState]:
    """Remove a segment from the segment manager.

    This handler removes a segment by ID and enforces the minimum segment limit.
    It also re-indexes remaining segments to maintain sequential IDs.

    Args:
        segment_id: ID of segment to remove (e.g., "0", "1", "2")
        segment_manager_state: Current segment manager state dict
        ui_state: Current UI state

    Returns:
        Tuple of:
            - Updated segment_manager_state dict
            - Status message string
            - Updated ui_state

    Notes:
        - Enforces min_segments limit (default 1)
        - Re-indexes remaining segments (0, 1, 2, ...)
        - Returns error message if at minimum capacity
        - Returns error message if segment ID not found

    Examples:
        >>> # Remove segment 1 from a 3-segment list
        >>> state = {
        ...     "segments": [seg0, seg1, seg2],
        ...     "next_segment_id": 3,
        ...     "max_segments": 10,
        ...     "min_segments": 1
        ... }
        >>> new_state, msg, ui_state = remove_segment_handler("1", state, UIState())
        >>> print(msg)
        'Segment 1 removed. Total: 2 segment(s).'
    """
    # Extract current state
    current_segments = segment_manager_state.get("segments", [])
    min_segments = segment_manager_state.get("min_segments", 1)
    next_id = segment_manager_state.get("next_segment_id", 0)
    max_segments = segment_manager_state.get("max_segments", 10)

    # Check if at minimum capacity
    if len(current_segments) <= min_segments:
        logger.warning(f"Cannot remove segment: at minimum capacity ({min_segments})")
        return (
            segment_manager_state,
            f"Minimum {min_segments} segment(s) required.",
            ui_state,
        )

    # Find segment to remove
    segment_to_remove: Any = None
    segment_index: int | None = None

    for i, seg in enumerate(current_segments):
        if isinstance(seg, SegmentUIComponents) and seg.segment_id == segment_id:
            segment_to_remove = seg
            segment_index = i
            break
        elif isinstance(seg, dict) and seg.get("segment_id") == segment_id:
            segment_to_remove = seg
            segment_index = i
            break

    if segment_to_remove is None or segment_index is None:
        logger.error(f"Segment ID {segment_id} not found")
        return (
            segment_manager_state,
            f"Segment {segment_id} not found.",
            ui_state,
        )

    # Remove segment
    logger.info(f"Removing segment {segment_id} at index {segment_index}")
    updated_segments = current_segments[:segment_index] + current_segments[segment_index + 1 :]

    # Re-index remaining segments (0, 1, 2, ...)
    for i, seg in enumerate(updated_segments):
        new_id = str(i)
        if isinstance(seg, SegmentUIComponents):
            seg.segment_id = new_id
        elif isinstance(seg, dict):
            seg["segment_id"] = new_id
        logger.debug(f"Re-indexed segment: old index {i}, new ID {new_id}")

    # Update state
    updated_state = {
        "segments": updated_segments,
        "next_segment_id": next_id,  # Don't decrement (keep IDs unique)
        "max_segments": max_segments,
        "min_segments": min_segments,
    }

    # Create status message
    new_count = len(updated_segments)
    message = f"Segment {segment_id} removed. Total: {new_count} segment(s)."

    return updated_state, message, ui_state


def get_segment_count(segment_manager_state: dict[str, Any]) -> int:
    """Get the current number of segments.

    Args:
        segment_manager_state: Segment manager state dict

    Returns:
        Number of segments currently in the manager

    Examples:
        >>> state = {"segments": [seg1, seg2, seg3]}
        >>> get_segment_count(state)
        3
    """
    return len(segment_manager_state.get("segments", []))


def can_add_segment(segment_manager_state: dict[str, Any]) -> bool:
    """Check if a new segment can be added.

    Args:
        segment_manager_state: Segment manager state dict

    Returns:
        True if under max_segments limit, False otherwise

    Examples:
        >>> state = {"segments": [seg1], "max_segments": 10}
        >>> can_add_segment(state)
        True
        >>> state = {"segments": [seg1] * 10, "max_segments": 10}
        >>> can_add_segment(state)
        False
    """
    current_count = get_segment_count(segment_manager_state)
    max_segments: int = segment_manager_state.get("max_segments", 10)
    return bool(current_count < max_segments)


def can_remove_segment(segment_manager_state: dict[str, Any]) -> bool:
    """Check if a segment can be removed.

    Args:
        segment_manager_state: Segment manager state dict

    Returns:
        True if above min_segments limit, False otherwise

    Examples:
        >>> state = {"segments": [seg1, seg2], "min_segments": 1}
        >>> can_remove_segment(state)
        True
        >>> state = {"segments": [seg1], "min_segments": 1}
        >>> can_remove_segment(state)
        False
    """
    current_count = get_segment_count(segment_manager_state)
    min_segments: int = segment_manager_state.get("min_segments", 1)
    return bool(current_count > min_segments)


__all__ = [
    "add_segment_handler",
    "remove_segment_handler",
    "get_segment_count",
    "can_add_segment",
    "can_remove_segment",
]
