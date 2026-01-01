"""Session-based workspace management for organizing outputs by request."""

import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional


class SessionWorkspace:
    """
    Manages session-specific workspace directories.

    Each request gets its own timestamped subdirectory:
    workspace/YYYYMMDD_HHMMSS_<short_description>/
    """

    _instance: Optional["SessionWorkspace"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._base_workspace: Optional[Path] = None
        self._current_session_path: Optional[Path] = None
        self._initialized = True

    def set_base_workspace(self, path: Path) -> None:
        """Set the base workspace root directory."""
        self._base_workspace = path
        path.mkdir(parents=True, exist_ok=True)

    def create_session(self, prompt: str, max_desc_length: int = 20) -> Path:
        """
        Create a new session directory based on timestamp and prompt.

        Args:
            prompt: User's input prompt (used to generate short description)
            max_desc_length: Maximum length for the description part

        Returns:
            Path to the created session directory
        """
        if self._base_workspace is None:
            raise RuntimeError("Base workspace not set. Call set_base_workspace first.")

        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Generate short description from prompt
        short_desc = self._generate_short_description(prompt, max_desc_length)

        # Create directory name
        if short_desc:
            dir_name = f"{timestamp}_{short_desc}"
        else:
            dir_name = timestamp

        # Create the session directory
        session_path = self._base_workspace / dir_name
        session_path.mkdir(parents=True, exist_ok=True)

        self._current_session_path = session_path
        return session_path

    def _generate_short_description(self, prompt: str, max_length: int) -> str:
        """
        Generate a short, filesystem-safe description from the prompt.

        Args:
            prompt: The user's input prompt
            max_length: Maximum length for the description

        Returns:
            A sanitized short description
        """
        if not prompt:
            return ""

        # Take first line or first sentence
        first_line = prompt.split('\n')[0].strip()

        # Remove common prefixes
        prefixes_to_remove = ['请', '帮我', '帮忙', '我想', '我要', '需要']
        for prefix in prefixes_to_remove:
            if first_line.startswith(prefix):
                first_line = first_line[len(prefix):]

        # Keep only safe characters (Chinese, alphanumeric, underscore, hyphen)
        safe_desc = re.sub(r'[^\w\u4e00-\u9fff\-]', '', first_line)

        # Truncate to max length
        if len(safe_desc) > max_length:
            safe_desc = safe_desc[:max_length]

        return safe_desc

    @property
    def current_path(self) -> Optional[Path]:
        """Get the current session workspace path."""
        return self._current_session_path

    @property
    def base_path(self) -> Optional[Path]:
        """Get the base workspace path."""
        return self._base_workspace

    def get_working_directory(self) -> Path:
        """
        Get the current working directory for file operations.

        Returns session path if available, otherwise base workspace.
        """
        if self._current_session_path:
            return self._current_session_path
        if self._base_workspace:
            return self._base_workspace
        raise RuntimeError("No workspace configured")

    def reset_session(self) -> None:
        """Reset the current session (for new requests)."""
        self._current_session_path = None


# Global singleton instance
session_workspace = SessionWorkspace()
