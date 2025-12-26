"""Unit tests for segment state management."""

from pipeworks.ui.handlers.segments import (
    add_segment_handler,
    can_add_segment,
    can_remove_segment,
    get_segment_count,
    remove_segment_handler,
)
from pipeworks.ui.models import SegmentManagerState, UIState


class TestSegmentManagerState:
    """Tests for SegmentManagerState dataclass."""

    def test_default_initialization(self):
        """Test SegmentManagerState initializes with correct defaults."""
        state = SegmentManagerState()

        assert state.segments == []
        assert state.next_segment_id == 0
        assert state.max_segments == 10
        assert state.min_segments == 1

    def test_custom_initialization(self):
        """Test SegmentManagerState with custom values."""
        state = SegmentManagerState(
            segments=[1, 2, 3],
            next_segment_id=5,
            max_segments=20,
            min_segments=2,
        )

        assert len(state.segments) == 3
        assert state.next_segment_id == 5
        assert state.max_segments == 20
        assert state.min_segments == 2

    def test_segments_list_mutable(self):
        """Test segments list is mutable."""
        state = SegmentManagerState()
        state.segments.append("test")

        assert len(state.segments) == 1
        assert state.segments[0] == "test"


class TestUIStateWithSegmentManager:
    """Tests for UIState with segment_manager field."""

    def test_ui_state_includes_segment_manager(self):
        """Test UIState includes segment_manager field."""
        state = UIState()

        assert hasattr(state, "segment_manager")
        assert isinstance(state.segment_manager, SegmentManagerState)

    def test_ui_state_segment_manager_default(self):
        """Test UIState segment_manager has correct defaults."""
        state = UIState()

        assert state.segment_manager.segments == []
        assert state.segment_manager.next_segment_id == 0
        assert state.segment_manager.max_segments == 10
        assert state.segment_manager.min_segments == 1


class TestGetSegmentCount:
    """Tests for get_segment_count utility."""

    def test_empty_segments(self):
        """Test count with no segments."""
        state_dict = {"segments": []}
        assert get_segment_count(state_dict) == 0

    def test_multiple_segments(self):
        """Test count with multiple segments."""
        state_dict = {"segments": [1, 2, 3, 4, 5]}
        assert get_segment_count(state_dict) == 5

    def test_missing_segments_key(self):
        """Test count with missing segments key defaults to 0."""
        state_dict = {}
        assert get_segment_count(state_dict) == 0


class TestCanAddSegment:
    """Tests for can_add_segment utility."""

    def test_can_add_when_under_limit(self):
        """Test can add when under max_segments."""
        state_dict = {"segments": [1, 2, 3], "max_segments": 10}
        assert can_add_segment(state_dict) is True

    def test_cannot_add_at_limit(self):
        """Test cannot add when at max_segments."""
        state_dict = {"segments": [1] * 10, "max_segments": 10}
        assert can_add_segment(state_dict) is False

    def test_cannot_add_over_limit(self):
        """Test cannot add when over max_segments."""
        state_dict = {"segments": [1] * 12, "max_segments": 10}
        assert can_add_segment(state_dict) is False

    def test_default_max_segments(self):
        """Test uses default max_segments of 10."""
        state_dict = {"segments": [1] * 9}
        assert can_add_segment(state_dict) is True

        state_dict = {"segments": [1] * 10}
        assert can_add_segment(state_dict) is False


class TestCanRemoveSegment:
    """Tests for can_remove_segment utility."""

    def test_can_remove_when_above_minimum(self):
        """Test can remove when above min_segments."""
        state_dict = {"segments": [1, 2, 3], "min_segments": 1}
        assert can_remove_segment(state_dict) is True

    def test_cannot_remove_at_minimum(self):
        """Test cannot remove when at min_segments."""
        state_dict = {"segments": [1], "min_segments": 1}
        assert can_remove_segment(state_dict) is False

    def test_cannot_remove_below_minimum(self):
        """Test cannot remove when below min_segments."""
        state_dict = {"segments": [], "min_segments": 1}
        assert can_remove_segment(state_dict) is False

    def test_default_min_segments(self):
        """Test uses default min_segments of 1."""
        state_dict = {"segments": [1, 2]}
        assert can_remove_segment(state_dict) is True

        state_dict = {"segments": [1]}
        assert can_remove_segment(state_dict) is False


class TestAddSegmentHandler:
    """Tests for add_segment_handler function."""

    def test_add_first_segment(self):
        """Test adding first segment."""
        state_dict = {
            "segments": [],
            "next_segment_id": 0,
            "max_segments": 10,
        }
        ui_state = UIState()

        new_state, message, updated_ui_state = add_segment_handler(state_dict, ui_state)

        assert new_state["next_segment_id"] == 1
        assert "Segment 0 added" in message
        assert "Total: 1" in message

    def test_add_multiple_segments(self):
        """Test adding multiple segments increments ID."""
        state_dict = {
            "segments": ["seg0"],
            "next_segment_id": 1,
            "max_segments": 10,
        }
        ui_state = UIState()

        # Add second segment
        new_state, message, _ = add_segment_handler(state_dict, ui_state)
        assert new_state["next_segment_id"] == 2
        assert "Segment 1 added" in message
        assert "Total: 2" in message

        # Add third segment
        state_dict = {
            "segments": ["seg0", "seg1"],
            "next_segment_id": 2,
            "max_segments": 10,
        }
        new_state, message, _ = add_segment_handler(state_dict, ui_state)
        assert new_state["next_segment_id"] == 3
        assert "Segment 2 added" in message
        assert "Total: 3" in message

    def test_add_segment_at_max_capacity(self):
        """Test adding segment when at max capacity."""
        state_dict = {
            "segments": [f"seg{i}" for i in range(10)],
            "next_segment_id": 10,
            "max_segments": 10,
        }
        ui_state = UIState()

        new_state, message, _ = add_segment_handler(state_dict, ui_state)

        # Should return same state
        assert new_state["next_segment_id"] == 10
        assert "Maximum 10 segments" in message
        assert len(new_state["segments"]) == 10

    def test_add_segment_preserves_max_segments(self):
        """Test add_segment_handler preserves max_segments setting."""
        state_dict = {
            "segments": [],
            "next_segment_id": 0,
            "max_segments": 5,
        }
        ui_state = UIState()

        new_state, _, _ = add_segment_handler(state_dict, ui_state)
        assert new_state["max_segments"] == 5


class TestRemoveSegmentHandler:
    """Tests for remove_segment_handler function."""

    def test_remove_segment_by_id(self):
        """Test removing a segment by ID."""
        # Create mock segments with IDs
        seg0 = {"segment_id": "0"}
        seg1 = {"segment_id": "1"}
        seg2 = {"segment_id": "2"}

        state_dict = {
            "segments": [seg0, seg1, seg2],
            "next_segment_id": 3,
            "max_segments": 10,
            "min_segments": 1,
        }
        ui_state = UIState()

        new_state, message, _ = remove_segment_handler("1", state_dict, ui_state)

        assert len(new_state["segments"]) == 2
        assert "Segment 1 removed" in message
        assert "Total: 2" in message

    def test_remove_segment_reindexes_remaining(self):
        """Test removing segment re-indexes remaining segments."""
        seg0 = {"segment_id": "0"}
        seg1 = {"segment_id": "1"}
        seg2 = {"segment_id": "2"}

        state_dict = {
            "segments": [seg0, seg1, seg2],
            "next_segment_id": 3,
            "max_segments": 10,
            "min_segments": 1,
        }
        ui_state = UIState()

        # Remove middle segment
        new_state, _, _ = remove_segment_handler("1", state_dict, ui_state)

        # Remaining segments should be re-indexed to 0, 1
        assert new_state["segments"][0]["segment_id"] == "0"
        assert new_state["segments"][1]["segment_id"] == "1"  # Was seg2, now index 1

    def test_remove_segment_at_minimum(self):
        """Test removing segment when at minimum capacity."""
        seg0 = {"segment_id": "0"}

        state_dict = {
            "segments": [seg0],
            "next_segment_id": 1,
            "max_segments": 10,
            "min_segments": 1,
        }
        ui_state = UIState()

        new_state, message, _ = remove_segment_handler("0", state_dict, ui_state)

        # Should return same state
        assert len(new_state["segments"]) == 1
        assert "Minimum 1 segment" in message

    def test_remove_nonexistent_segment(self):
        """Test removing a segment that doesn't exist."""
        seg0 = {"segment_id": "0"}
        seg1 = {"segment_id": "1"}

        state_dict = {
            "segments": [seg0, seg1],
            "next_segment_id": 2,
            "max_segments": 10,
            "min_segments": 1,
        }
        ui_state = UIState()

        new_state, message, _ = remove_segment_handler("5", state_dict, ui_state)

        # Should return same state
        assert len(new_state["segments"]) == 2
        assert "not found" in message.lower()

    def test_remove_preserves_next_segment_id(self):
        """Test removing segment doesn't decrement next_segment_id."""
        seg0 = {"segment_id": "0"}
        seg1 = {"segment_id": "1"}
        seg2 = {"segment_id": "2"}

        state_dict = {
            "segments": [seg0, seg1, seg2],
            "next_segment_id": 5,  # Already incremented past current segments
            "max_segments": 10,
            "min_segments": 1,
        }
        ui_state = UIState()

        new_state, _, _ = remove_segment_handler("1", state_dict, ui_state)

        # next_segment_id should stay the same (unique IDs across session)
        assert new_state["next_segment_id"] == 5

    def test_remove_with_segment_ui_components(self):
        """Test removing segment when using SegmentUIComponents instances."""
        import gradio as gr

        with gr.Blocks():
            from pipeworks.ui.segment_plugins import CompleteSegmentPlugin

            plugin = CompleteSegmentPlugin()
            seg0 = plugin.create_ui("0", [])
            seg1 = plugin.create_ui("1", [])
            seg2 = plugin.create_ui("2", [])

            state_dict = {
                "segments": [seg0, seg1, seg2],
                "next_segment_id": 3,
                "max_segments": 10,
                "min_segments": 1,
            }
            ui_state = UIState()

            new_state, message, _ = remove_segment_handler("1", state_dict, ui_state)

            assert len(new_state["segments"]) == 2
            assert new_state["segments"][0].segment_id == "0"
            assert new_state["segments"][1].segment_id == "1"  # Re-indexed from 2


class TestSegmentHandlerIntegration:
    """Integration tests for segment handlers."""

    def test_add_and_remove_workflow(self):
        """Test complete workflow of adding and removing segments."""
        # Start with empty state
        state_dict = {
            "segments": [],
            "next_segment_id": 0,
            "max_segments": 10,
            "min_segments": 1,
        }
        ui_state = UIState()

        # Add first segment
        state_dict, msg, _ = add_segment_handler(state_dict, ui_state)
        assert "Segment 0 added" in msg
        assert state_dict["next_segment_id"] == 1

        # Simulate adding the segment to the list
        state_dict["segments"].append({"segment_id": "0"})

        # Add second segment
        state_dict, msg, _ = add_segment_handler(state_dict, ui_state)
        assert "Segment 1 added" in msg
        state_dict["segments"].append({"segment_id": "1"})

        # Add third segment
        state_dict, msg, _ = add_segment_handler(state_dict, ui_state)
        assert "Segment 2 added" in msg
        state_dict["segments"].append({"segment_id": "2"})

        # Should have 3 segments
        assert len(state_dict["segments"]) == 3
        assert state_dict["next_segment_id"] == 3

        # Remove middle segment
        state_dict, msg, _ = remove_segment_handler("1", state_dict, ui_state)
        assert "Segment 1 removed" in msg
        assert len(state_dict["segments"]) == 2

        # Verify re-indexing
        assert state_dict["segments"][0]["segment_id"] == "0"
        assert state_dict["segments"][1]["segment_id"] == "1"  # Was 2, now 1

    def test_enforce_limits(self):
        """Test that limits are properly enforced."""
        state_dict = {
            "segments": [],
            "next_segment_id": 0,
            "max_segments": 3,
            "min_segments": 1,
        }
        ui_state = UIState()

        # Add 3 segments
        for i in range(3):
            state_dict, msg, _ = add_segment_handler(state_dict, ui_state)
            state_dict["segments"].append({"segment_id": str(i)})

        # Try to add 4th segment (should fail)
        state_dict, msg, _ = add_segment_handler(state_dict, ui_state)
        assert "Maximum 3 segments" in msg
        assert len(state_dict["segments"]) == 3

        # Remove down to 1 segment
        state_dict, _, _ = remove_segment_handler("2", state_dict, ui_state)
        state_dict, _, _ = remove_segment_handler("1", state_dict, ui_state)

        # Try to remove last segment (should fail)
        state_dict, msg, _ = remove_segment_handler("0", state_dict, ui_state)
        assert "Minimum 1 segment" in msg
        assert len(state_dict["segments"]) == 1
