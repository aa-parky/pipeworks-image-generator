"""Unit tests for prompt handler functions."""

from unittest.mock import Mock

import pytest

from pipeworks.ui.handlers.prompt import build_combined_prompt
from pipeworks.ui.models import SegmentConfig, UIState


@pytest.fixture
def mock_state():
    """Create a mock UI state with prompt_builder."""
    state = UIState()
    state.prompt_builder = Mock()
    state.prompt_builder.get_full_path = Mock(return_value="/full/path/file.txt")
    state.prompt_builder.get_random_line = Mock(return_value="random content")
    state.prompt_builder.get_specific_line = Mock(return_value="specific content")
    state.prompt_builder.get_line_range = Mock(return_value="range content")
    state.prompt_builder.get_all_lines = Mock(return_value="all content")
    state.prompt_builder.get_random_lines = Mock(return_value="multi content")
    state.prompt_builder.get_sequential_line = Mock(return_value="sequential content")
    state.prompt_builder.build_prompt = Mock(return_value="final prompt")
    return state


@pytest.fixture
def empty_segments():
    """Create 9 empty segments for testing."""
    return [SegmentConfig() for _ in range(9)]


class TestAddSegmentLogic:
    """Tests for add_segment() logic within build_combined_prompt()."""

    def test_text_only_segment(self, mock_state, empty_segments):
        """Test segment with only text (no file)."""
        start_1 = SegmentConfig(text="wizard")
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        # Should call build_prompt with a text segment
        mock_state.prompt_builder.build_prompt.assert_called_once()
        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert len(segments) == 1
        assert segments[0] == ("text", "wizard")

    def test_file_only_segment(self, mock_state, empty_segments):
        """Test segment with only file (no text)."""
        start_1 = SegmentConfig(file="test.txt", mode="Random Line")
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        # Should call build_prompt with a file_random segment
        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert len(segments) == 1
        assert segments[0][0] == "file_random"

    def test_text_first_order(self, mock_state, empty_segments):
        """Test text_first order combines text before file content."""
        start_1 = SegmentConfig(
            text="wizard",
            file="test.txt",
            mode="Random Line",
            text_order="text_first",
            delimiter=", ",
        )
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        # Should combine text + delimiter + file_content
        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert len(segments) == 1
        assert segments[0] == ("text", "wizard, random content")

    def test_file_first_order(self, mock_state, empty_segments):
        """Test file_first order combines file content before text."""
        start_1 = SegmentConfig(
            text="wizard",
            file="test.txt",
            mode="Random Line",
            text_order="file_first",
            delimiter=", ",
        )
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        # Should combine file_content + delimiter + text
        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert len(segments) == 1
        assert segments[0] == ("text", "random content, wizard")

    def test_custom_delimiter_period_space(self, mock_state, empty_segments):
        """Test custom delimiter '. ' (period-space)."""
        start_1 = SegmentConfig(
            text="a wizard",
            file="test.txt",
            mode="Random Line",
            text_order="text_first",
            delimiter=". ",
        )
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert segments[0] == ("text", "a wizard. random content")

    def test_custom_delimiter_space_only(self, mock_state, empty_segments):
        """Test custom delimiter ' ' (single space)."""
        start_1 = SegmentConfig(
            text="wizard",
            file="test.txt",
            mode="Random Line",
            text_order="text_first",
            delimiter=" ",
        )
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert segments[0] == ("text", "wizard random content")

    def test_custom_delimiter_comma_only(self, mock_state, empty_segments):
        """Test custom delimiter ',' (comma only)."""
        start_1 = SegmentConfig(
            text="wizard",
            file="test.txt",
            mode="Random Line",
            text_order="text_first",
            delimiter=",",
        )
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert segments[0] == ("text", "wizard,random content")

    def test_custom_delimiter_period_only(self, mock_state, empty_segments):
        """Test custom delimiter '.' (period only)."""
        start_1 = SegmentConfig(
            text="wizard",
            file="test.txt",
            mode="Random Line",
            text_order="text_first",
            delimiter=".",
        )
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert segments[0] == ("text", "wizard.random content")

    def test_empty_segment(self, mock_state, empty_segments):
        """Test segment with no text and no file is skipped."""
        start_1 = SegmentConfig()
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        # Should not add any segments
        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert len(segments) == 0

    def test_whitespace_only_text_skipped(self, mock_state, empty_segments):
        """Test segment with whitespace-only text is skipped."""
        start_1 = SegmentConfig(text="   \n\t  ")
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert len(segments) == 0

    def test_file_read_failure_falls_back_to_text(self, mock_state, empty_segments):
        """Test that if file read fails, we fall back to text only."""
        mock_state.prompt_builder.get_random_line = Mock(return_value="")  # Empty = failure

        start_1 = SegmentConfig(
            text="wizard",
            file="test.txt",
            mode="Random Line",
            text_order="text_first",
            delimiter=", ",
        )
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        # Should fall back to text only
        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert len(segments) == 1
        assert segments[0] == ("text", "wizard")

    def test_specific_line_mode_with_both_text_and_file(self, mock_state, empty_segments):
        """Test Specific Line mode with both text and file."""
        start_1 = SegmentConfig(
            text="wizard",
            file="test.txt",
            mode="Specific Line",
            line=5,
            text_order="text_first",
            delimiter=", ",
        )
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        # Should call get_specific_line with line number
        mock_state.prompt_builder.get_specific_line.assert_called_once_with(
            "/full/path/file.txt", 5
        )
        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert segments[0] == ("text", "wizard, specific content")

    def test_line_range_mode_with_both_text_and_file(self, mock_state, empty_segments):
        """Test Line Range mode with both text and file."""
        start_1 = SegmentConfig(
            text="wizard",
            file="test.txt",
            mode="Line Range",
            line=1,
            range_end=5,
            text_order="text_first",
            delimiter=", ",
        )
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        # Should call get_line_range
        mock_state.prompt_builder.get_line_range.assert_called_once_with(
            "/full/path/file.txt", 1, 5
        )
        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert segments[0] == ("text", "wizard, range content")

    def test_all_lines_mode_with_both_text_and_file(self, mock_state, empty_segments):
        """Test All Lines mode with both text and file."""
        start_1 = SegmentConfig(
            text="wizard",
            file="test.txt",
            mode="All Lines",
            text_order="text_first",
            delimiter=", ",
        )
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        # Should call get_all_lines
        mock_state.prompt_builder.get_all_lines.assert_called_once_with("/full/path/file.txt")
        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert segments[0] == ("text", "wizard, all content")

    def test_random_multiple_mode_with_both_text_and_file(self, mock_state, empty_segments):
        """Test Random Multiple mode with both text and file."""
        start_1 = SegmentConfig(
            text="wizard",
            file="test.txt",
            mode="Random Multiple",
            count=3,
            text_order="text_first",
            delimiter=", ",
        )
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        # Should call get_random_lines
        mock_state.prompt_builder.get_random_lines.assert_called_once_with("/full/path/file.txt", 3)
        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert segments[0] == ("text", "wizard, multi content")

    def test_sequential_mode_with_both_text_and_file(self, mock_state, empty_segments):
        """Test Sequential mode with both text and file."""
        start_1 = SegmentConfig(
            text="wizard",
            file="test.txt",
            mode="Sequential",
            sequential_start_line=10,
            text_order="text_first",
            delimiter=", ",
        )
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state, run_index=2)

        # Should call get_sequential_line with run_index
        mock_state.prompt_builder.get_sequential_line.assert_called_once_with(
            "/full/path/file.txt", 10, 2
        )
        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert segments[0] == ("text", "wizard, sequential content")

    def test_multiple_segments_combined(self, mock_state, empty_segments):
        """Test multiple segments with different settings."""
        start_1 = SegmentConfig(
            text="wizard",
            file="test.txt",
            mode="Random Line",
            text_order="text_first",
            delimiter=". ",
        )
        start_2 = SegmentConfig(text="castle")
        start_3 = SegmentConfig(file="colors.txt", mode="Random Line")

        result = build_combined_prompt(
            start_1, start_2, start_3, *empty_segments[3:], state=mock_state
        )

        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert len(segments) == 3
        assert segments[0] == ("text", "wizard. random content")
        assert segments[1] == ("text", "castle")
        assert segments[2][0] == "file_random"

    def test_text_strips_whitespace(self, mock_state, empty_segments):
        """Test that text whitespace is stripped."""
        start_1 = SegmentConfig(text="  wizard  ")
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert segments[0] == ("text", "wizard")

    def test_combined_text_strips_whitespace(self, mock_state, empty_segments):
        """Test that whitespace is stripped in combined segments."""
        start_1 = SegmentConfig(
            text="  wizard  ",
            file="test.txt",
            mode="Random Line",
            text_order="text_first",
            delimiter=", ",
        )
        result = build_combined_prompt(start_1, *empty_segments[1:], state=mock_state)

        segments = mock_state.prompt_builder.build_prompt.call_args[0][0]
        assert segments[0] == ("text", "wizard, random content")
