"""
Input Validator - Security validation for PTY input.

Prevents malicious escape sequences and oversized inputs from being
piped to Claude Code process. Based on OWASP guidelines and terminal
security research.

Key security concerns addressed:
- Buffer overflow via oversized inputs (max 2KB per message)
- Terminal title spoofing via OSC title sequences
- Clipboard manipulation via OSC 52
- Key remapping via DCS/DECUDK sequences
- Color palette modification for UI deception

Usage:
    from wxcode.services.input_validator import validate_input, sanitize_input

    is_valid, error = validate_input(user_data)
    if not is_valid:
        logger.warning(f"Rejected input: {error}")
        return

    # Or use sanitization for less strict handling
    safe_data = sanitize_input(user_data)
    await pty.write(safe_data)
"""

import re
from typing import Optional

__all__ = [
    "validate_input",
    "sanitize_input",
    "InputValidationError",
    "MAX_MESSAGE_SIZE",
    "MAX_INPUT_RATE",
    "is_control_sequence",
    "get_control_signal",
    "CONTROL_TO_SIGNAL",
    "DANGEROUS_SEQUENCES",
]


class InputValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, message: str, reason: str):
        """
        Initialize validation error.

        Args:
            message: Human-readable error message
            reason: Machine-readable reason code
        """
        super().__init__(message)
        self.reason = reason


# Maximum single message size: 2KB (prevent buffer overflow attempts)
MAX_MESSAGE_SIZE = 2 * 1024

# Maximum input rate: 10KB/second (for rate limiting in caller)
MAX_INPUT_RATE = 10 * 1024

# Dangerous escape sequences to filter
# Based on terminal escape injection research and OWASP guidelines
# Reference: 24-RESEARCH.md lines 533-568

# Patterns for DETECTION (just need to find the start of dangerous sequence)
# Used by validate_input() to reject any input containing these patterns
DANGEROUS_SEQUENCES = [
    # OSC (Operating System Command) sequences
    re.compile(rb"\x1b\]0;"),      # OSC 0: Title change (can spoof prompts)
    re.compile(rb"\x1b\]52;"),     # OSC 52: Clipboard manipulation
    re.compile(rb"\x1b\]4;"),      # OSC 4: Color palette modification
    re.compile(rb"\x1b\]10;"),     # OSC 10: Foreground color change
    re.compile(rb"\x1b\]11;"),     # OSC 11: Background color change

    # DCS (Device Control String) sequences
    re.compile(rb"\x1bP"),         # DCS: Device control string start

    # CSI (Control Sequence Introducer) dangerous patterns
    re.compile(rb"\x1b\[.*?p"),    # Key remapping (DECUDK - user-defined keys)
    re.compile(rb"\x1b\[!p"),      # Soft terminal reset (DECSTR)
]

# Patterns for SANITIZATION (match full sequence for removal)
# Used by sanitize_input() to strip dangerous sequences while keeping safe content
# OSC sequences end with BEL (\x07) or ST (\x1b\\)
# DCS sequences end with ST (\x1b\\)
_SANITIZE_PATTERNS = [
    # OSC sequences: ESC ] N ; ... (BEL | ST)
    re.compile(rb"\x1b\]0;[^\x07\x1b]*(?:\x07|\x1b\\)?"),      # OSC 0: Title
    re.compile(rb"\x1b\]52;[^\x07\x1b]*(?:\x07|\x1b\\)?"),     # OSC 52: Clipboard
    re.compile(rb"\x1b\]4;[^\x07\x1b]*(?:\x07|\x1b\\)?"),      # OSC 4: Color palette
    re.compile(rb"\x1b\]10;[^\x07\x1b]*(?:\x07|\x1b\\)?"),     # OSC 10: Foreground
    re.compile(rb"\x1b\]11;[^\x07\x1b]*(?:\x07|\x1b\\)?"),     # OSC 11: Background

    # DCS sequences: ESC P ... ST
    re.compile(rb"\x1bP[^\x1b]*(?:\x1b\\)?"),                  # DCS

    # CSI dangerous patterns
    re.compile(rb"\x1b\[.*?p"),    # Key remapping
    re.compile(rb"\x1b\[!p"),      # Soft terminal reset
]


def validate_input(data: bytes) -> tuple[bool, Optional[str]]:
    """
    Validate terminal input for security.

    Checks for:
    1. Size limits (max 2KB per message)
    2. Dangerous escape sequences that could compromise terminal

    Args:
        data: Raw bytes to validate

    Returns:
        Tuple of (is_valid, error_message or None)

    Examples:
        >>> validate_input(b"hello")
        (True, None)
        >>> validate_input(b"x" * 3000)
        (False, "Input too large: 3000 bytes (max 2048)")
        >>> validate_input(b"\\x1b]0;malicious\\x07")
        (False, "Potentially dangerous escape sequence detected")
    """
    # Check size limit
    if len(data) > MAX_MESSAGE_SIZE:
        return False, f"Input too large: {len(data)} bytes (max {MAX_MESSAGE_SIZE})"

    # Check for dangerous escape sequences
    for pattern in DANGEROUS_SEQUENCES:
        if pattern.search(data):
            return False, "Potentially dangerous escape sequence detected"

    return True, None


def sanitize_input(data: bytes) -> bytes:
    """
    Remove dangerous escape sequences from input.

    Use this as alternative to rejection when you want to allow
    the input but strip dangerous parts. Safe ANSI sequences
    (colors, cursor movement) are preserved.

    Args:
        data: Raw bytes to sanitize

    Returns:
        Sanitized bytes with dangerous sequences removed

    Examples:
        >>> sanitize_input(b"hello world")
        b'hello world'
        >>> sanitize_input(b"before\\x1b]0;title\\x07after")
        b'beforeafter'
    """
    result = data
    for pattern in _SANITIZE_PATTERNS:
        result = pattern.sub(b"", result)
    return result


def is_control_sequence(data: bytes) -> bool:
    """
    Check if data is a terminal control sequence.

    Useful for detecting Ctrl+C (0x03), Ctrl+D (0x04), etc.
    Control characters are in the range 0x00-0x1F.

    Args:
        data: Raw bytes to check

    Returns:
        True if data is a single control character

    Examples:
        >>> is_control_sequence(b"\\x03")  # Ctrl+C
        True
        >>> is_control_sequence(b"a")
        False
        >>> is_control_sequence(b"\\x03\\x03")  # Multiple bytes
        False
    """
    if len(data) == 1:
        byte = data[0]
        # Control characters are 0x00-0x1F
        return 0 <= byte <= 0x1F
    return False


# Map of common control sequences to signal names
# Used for handling special key combinations in PTY input
CONTROL_TO_SIGNAL = {
    b"\x03": "SIGINT",   # Ctrl+C - Interrupt
    b"\x04": "EOF",      # Ctrl+D - End of file
    b"\x1a": "SIGTSTP",  # Ctrl+Z - Suspend
    b"\x1c": "SIGQUIT",  # Ctrl+\ - Quit with core dump
}


def get_control_signal(data: bytes) -> Optional[str]:
    """
    Get signal name for control sequence if applicable.

    Maps common control key combinations to their corresponding
    signal names for special handling in PTY sessions.

    Args:
        data: Raw bytes (should be single control character)

    Returns:
        Signal name or None if not a recognized control sequence

    Examples:
        >>> get_control_signal(b"\\x03")
        'SIGINT'
        >>> get_control_signal(b"\\x04")
        'EOF'
        >>> get_control_signal(b"a")
        None
    """
    return CONTROL_TO_SIGNAL.get(data)
