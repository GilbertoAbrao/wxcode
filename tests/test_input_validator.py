"""
Unit tests for input validation.

Tests cover:
- validate_input: size limits, dangerous sequence detection
- sanitize_input: safe content preservation, sequence removal
- is_control_sequence: control character detection
- get_control_signal: control to signal mapping
- All DANGEROUS_SEQUENCES patterns
"""

import pytest

from wxcode.services.input_validator import (
    validate_input,
    sanitize_input,
    InputValidationError,
    MAX_MESSAGE_SIZE,
    is_control_sequence,
    get_control_signal,
    DANGEROUS_SEQUENCES,
    CONTROL_TO_SIGNAL,
)


class TestValidateInput:
    """Test cases for validate_input function."""

    def test_valid_simple_text(self):
        """Test valid simple text input."""
        is_valid, error = validate_input(b"hello world")
        assert is_valid is True
        assert error is None

    def test_valid_utf8(self):
        """Test valid UTF-8 input."""
        is_valid, error = validate_input("ola mundo".encode("utf-8"))
        assert is_valid is True
        assert error is None

    def test_valid_utf8_with_accents(self):
        """Test valid UTF-8 input with accents."""
        is_valid, error = validate_input("cafe, ecole, nino".encode("utf-8"))
        assert is_valid is True
        assert error is None

    def test_valid_newlines(self):
        """Test input with newlines is valid."""
        is_valid, error = validate_input(b"line1\nline2\r\nline3")
        assert is_valid is True
        assert error is None

    def test_valid_control_c(self):
        """Test Ctrl+C is valid (not a dangerous sequence)."""
        is_valid, error = validate_input(b"\x03")
        assert is_valid is True

    def test_valid_control_d(self):
        """Test Ctrl+D is valid."""
        is_valid, error = validate_input(b"\x04")
        assert is_valid is True

    def test_valid_tab_and_backspace(self):
        """Test tab and backspace are valid."""
        is_valid, error = validate_input(b"hello\tworld\x08")
        assert is_valid is True

    def test_valid_empty_input(self):
        """Test empty input is valid."""
        is_valid, error = validate_input(b"")
        assert is_valid is True

    def test_invalid_too_large(self):
        """Test rejection of oversized input."""
        large_input = b"x" * (MAX_MESSAGE_SIZE + 1)
        is_valid, error = validate_input(large_input)
        assert is_valid is False
        assert "too large" in error.lower()

    def test_invalid_exactly_at_limit(self):
        """Test input exactly at limit is valid."""
        exactly_max = b"x" * MAX_MESSAGE_SIZE
        is_valid, error = validate_input(exactly_max)
        assert is_valid is True

    def test_invalid_osc_title(self):
        """Test rejection of OSC title change."""
        malicious = b"\x1b]0;malicious title\x07"
        is_valid, error = validate_input(malicious)
        assert is_valid is False
        assert "escape sequence" in error.lower()

    def test_invalid_osc_clipboard(self):
        """Test rejection of clipboard manipulation."""
        malicious = b"\x1b]52;c;base64data\x07"
        is_valid, error = validate_input(malicious)
        assert is_valid is False

    def test_invalid_dcs(self):
        """Test rejection of device control string."""
        malicious = b"\x1bPsome control\x1b\\"
        is_valid, error = validate_input(malicious)
        assert is_valid is False

    def test_invalid_key_remapping(self):
        """Test rejection of key remapping sequence."""
        # DECUDK: ESC [ Ps ; Ps | Ps / Ps p - user defined keys
        malicious = b"\x1b[0p"
        is_valid, error = validate_input(malicious)
        assert is_valid is False

    def test_invalid_embedded_in_text(self):
        """Test rejection when dangerous sequence embedded in text."""
        mixed = b"normal text \x1b]0;title\x07 more text"
        is_valid, error = validate_input(mixed)
        assert is_valid is False

    def test_invalid_soft_reset(self):
        """Test rejection of soft terminal reset."""
        malicious = b"\x1b[!p"
        is_valid, error = validate_input(malicious)
        assert is_valid is False

    def test_invalid_color_palette(self):
        """Test rejection of color palette modification."""
        malicious = b"\x1b]4;1;rgb:ff/00/00\x07"
        is_valid, error = validate_input(malicious)
        assert is_valid is False

    def test_invalid_foreground_color(self):
        """Test rejection of foreground color change."""
        malicious = b"\x1b]10;#ffffff\x07"
        is_valid, error = validate_input(malicious)
        assert is_valid is False

    def test_invalid_background_color(self):
        """Test rejection of background color change."""
        malicious = b"\x1b]11;#000000\x07"
        is_valid, error = validate_input(malicious)
        assert is_valid is False


class TestSanitizeInput:
    """Test cases for sanitize_input function."""

    def test_sanitize_clean_text(self):
        """Test clean text passes through unchanged."""
        result = sanitize_input(b"hello world")
        assert result == b"hello world"

    def test_sanitize_removes_osc_title(self):
        """Test removal of OSC title sequence."""
        input_bytes = b"before\x1b]0;title\x07after"
        result = sanitize_input(input_bytes)
        assert b"\x1b]0;" not in result
        assert b"before" in result
        assert b"after" in result

    def test_sanitize_removes_osc_title_with_st(self):
        """Test removal of OSC title sequence with ST terminator."""
        input_bytes = b"before\x1b]0;title\x1b\\after"
        result = sanitize_input(input_bytes)
        assert b"before" in result
        assert b"after" in result

    def test_sanitize_removes_multiple_sequences(self):
        """Test removal of multiple dangerous sequences."""
        input_bytes = b"\x1b]0;a\x07text\x1b]52;b\x07more"
        result = sanitize_input(input_bytes)
        assert b"\x1b]0;" not in result
        assert b"\x1b]52;" not in result
        assert b"text" in result
        assert b"more" in result

    def test_sanitize_preserves_safe_ansi(self):
        """Test that common ANSI codes are preserved."""
        # Color codes should be preserved (not in dangerous list)
        input_bytes = b"\x1b[32mgreen\x1b[0m"
        result = sanitize_input(input_bytes)
        assert result == input_bytes

    def test_sanitize_preserves_cursor_movement(self):
        """Test that cursor movement codes are preserved."""
        input_bytes = b"\x1b[2J\x1b[H"  # Clear screen and home
        result = sanitize_input(input_bytes)
        assert result == input_bytes

    def test_sanitize_removes_dcs(self):
        """Test removal of DCS sequence."""
        input_bytes = b"before\x1bPdata\x1b\\after"
        result = sanitize_input(input_bytes)
        assert b"\x1bP" not in result

    def test_sanitize_removes_clipboard(self):
        """Test removal of clipboard manipulation."""
        input_bytes = b"text\x1b]52;c;base64\x07rest"
        result = sanitize_input(input_bytes)
        assert b"\x1b]52;" not in result
        assert b"text" in result
        assert b"rest" in result

    def test_sanitize_removes_key_remapping(self):
        """Test removal of key remapping sequence."""
        input_bytes = b"before\x1b[0;59;ap after"
        result = sanitize_input(input_bytes)
        assert b"before" in result
        assert b"after" in result

    def test_sanitize_empty_input(self):
        """Test sanitizing empty input."""
        result = sanitize_input(b"")
        assert result == b""

    def test_sanitize_only_dangerous(self):
        """Test sanitizing input that is only dangerous sequence."""
        result = sanitize_input(b"\x1b]0;title\x07")
        assert result == b""


class TestControlSequences:
    """Test cases for control sequence detection."""

    def test_is_control_ctrl_c(self):
        """Test Ctrl+C detection."""
        assert is_control_sequence(b"\x03") is True

    def test_is_control_ctrl_d(self):
        """Test Ctrl+D detection."""
        assert is_control_sequence(b"\x04") is True

    def test_is_control_ctrl_z(self):
        """Test Ctrl+Z detection."""
        assert is_control_sequence(b"\x1a") is True

    def test_is_control_ctrl_backslash(self):
        """Test Ctrl+\\ detection."""
        assert is_control_sequence(b"\x1c") is True

    def test_is_control_null(self):
        """Test null byte is a control character."""
        assert is_control_sequence(b"\x00") is True

    def test_is_control_escape(self):
        """Test escape is a control character."""
        assert is_control_sequence(b"\x1b") is True

    def test_is_control_regular_char(self):
        """Test regular character is not control."""
        assert is_control_sequence(b"a") is False

    def test_is_control_space(self):
        """Test space is not a control character."""
        assert is_control_sequence(b" ") is False

    def test_is_control_multi_byte(self):
        """Test multi-byte is not single control."""
        assert is_control_sequence(b"\x03\x03") is False

    def test_is_control_empty(self):
        """Test empty bytes is not control."""
        assert is_control_sequence(b"") is False

    def test_get_signal_ctrl_c(self):
        """Test Ctrl+C maps to SIGINT."""
        assert get_control_signal(b"\x03") == "SIGINT"

    def test_get_signal_ctrl_d(self):
        """Test Ctrl+D maps to EOF."""
        assert get_control_signal(b"\x04") == "EOF"

    def test_get_signal_ctrl_z(self):
        """Test Ctrl+Z maps to SIGTSTP."""
        assert get_control_signal(b"\x1a") == "SIGTSTP"

    def test_get_signal_ctrl_backslash(self):
        """Test Ctrl+\\ maps to SIGQUIT."""
        assert get_control_signal(b"\x1c") == "SIGQUIT"

    def test_get_signal_unknown(self):
        """Test unknown returns None."""
        assert get_control_signal(b"\x01") is None
        assert get_control_signal(b"a") is None

    def test_get_signal_empty(self):
        """Test empty bytes returns None."""
        assert get_control_signal(b"") is None


class TestDangerousPatternsCoverage:
    """Ensure all dangerous patterns are tested."""

    @pytest.mark.parametrize("pattern,test_input", [
        ("osc_title", b"\x1b]0;x"),
        ("osc_clipboard", b"\x1b]52;x"),
        ("dcs", b"\x1bPx"),
        ("key_remap", b"\x1b[0p"),
        ("color_palette", b"\x1b]4;x"),
        ("fg_color", b"\x1b]10;x"),
        ("bg_color", b"\x1b]11;x"),
        ("soft_reset", b"\x1b[!p"),
    ])
    def test_dangerous_pattern(self, pattern, test_input):
        """Test each dangerous pattern is rejected."""
        is_valid, error = validate_input(test_input)
        assert is_valid is False, f"Pattern {pattern} should be rejected"

    def test_all_patterns_counted(self):
        """Test that we have expected number of dangerous patterns."""
        # 8 patterns: 5 OSC + 1 DCS + 2 CSI
        assert len(DANGEROUS_SEQUENCES) == 8

    def test_all_control_signals_mapped(self):
        """Test that we have expected control signal mappings."""
        # 4 mappings: Ctrl+C, Ctrl+D, Ctrl+Z, Ctrl+\\
        assert len(CONTROL_TO_SIGNAL) == 4


class TestInputValidationError:
    """Test cases for InputValidationError exception."""

    def test_error_has_reason(self):
        """Test that error includes reason attribute."""
        error = InputValidationError("Test message", "test_reason")
        assert error.reason == "test_reason"
        assert str(error) == "Test message"

    def test_error_can_be_raised(self):
        """Test that error can be raised and caught."""
        with pytest.raises(InputValidationError) as exc_info:
            raise InputValidationError("Validation failed", "size_exceeded")
        assert exc_info.value.reason == "size_exceeded"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_input_one_byte_under_limit(self):
        """Test input one byte under limit is valid."""
        data = b"x" * (MAX_MESSAGE_SIZE - 1)
        is_valid, error = validate_input(data)
        assert is_valid is True

    def test_input_one_byte_over_limit(self):
        """Test input one byte over limit is invalid."""
        data = b"x" * (MAX_MESSAGE_SIZE + 1)
        is_valid, error = validate_input(data)
        assert is_valid is False

    def test_dangerous_at_start(self):
        """Test dangerous sequence at start of input."""
        is_valid, error = validate_input(b"\x1b]0;x\x07safe text")
        assert is_valid is False

    def test_dangerous_at_end(self):
        """Test dangerous sequence at end of input."""
        is_valid, error = validate_input(b"safe text\x1b]0;x\x07")
        assert is_valid is False

    def test_incomplete_escape_sequence(self):
        """Test incomplete escape sequence (just ESC + bracket)."""
        # This is fine - not a complete dangerous sequence
        is_valid, error = validate_input(b"\x1b[")
        assert is_valid is True

    def test_binary_data(self):
        """Test binary data without escape sequences."""
        binary = bytes(range(0x20, 0x7f))  # Printable ASCII
        is_valid, error = validate_input(binary)
        assert is_valid is True
