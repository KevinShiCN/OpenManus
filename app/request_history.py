"""Request history module for tracking user prompts.

Automatically maintains a markdown file with all user requests for review.
"""

import os
from datetime import datetime
from pathlib import Path

from app.config import PROJECT_ROOT
from app.logger import logger


HISTORY_FILE = PROJECT_ROOT / "logs" / "request_history.md"


def _ensure_history_file():
    """Ensure the history file exists with proper header."""
    if not HISTORY_FILE.exists():
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write("# OpenManus Request History\n\n")
            f.write("> Auto-generated request log for review and debugging.\n\n")
            f.write("---\n\n")


def log_request(prompt: str, status: str = "started") -> str:
    """Log a user request to both logger and history file.

    Args:
        prompt: The user's input prompt
        status: Request status (started/completed/failed/interrupted)

    Returns:
        Request ID (timestamp-based)
    """
    _ensure_history_file()

    timestamp = datetime.now()
    request_id = timestamp.strftime("%Y%m%d_%H%M%S")
    formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # Log to standard logger
    logger.info(f"[REQUEST:{request_id}] {status.upper()} - {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

    if status == "started":
        # Append to history file
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"## [{request_id}] {formatted_time}\n\n")
            f.write(f"**Status:** `{status}`\n\n")
            f.write("**Prompt:**\n\n")
            f.write("```\n")
            f.write(prompt)
            f.write("\n```\n\n")
            f.write("---\n\n")

    return request_id


def update_request_status(request_id: str, status: str, result_summary: str = None):
    """Update the status of a request in the log.

    Args:
        request_id: The request ID returned by log_request
        status: New status (completed/failed/interrupted)
        result_summary: Optional summary of the result
    """
    logger.info(f"[REQUEST:{request_id}] {status.upper()}" + (f" - {result_summary}" if result_summary else ""))
