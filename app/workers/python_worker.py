"""
Lightweight worker module for python_execute.
This module is intentionally kept minimal to reduce subprocess import time.
DO NOT import heavy dependencies here (pydantic, browser_use, etc.)
"""

import sys
import time
from io import StringIO


def execute_code(code: str, submit_time: float) -> dict:
    """Execute Python code in a worker process."""
    worker_start = time.perf_counter()
    init_time_ms = (worker_start - submit_time) * 1000
    is_warm = init_time_ms < 100

    print(
        f"[python_worker] dispatch latency: {init_time_ms:.1f}ms "
        f"({'warm' if is_warm else 'cold'} start)",
        file=sys.stderr
    )

    original_stdout = sys.stdout
    try:
        output_buffer = StringIO()
        sys.stdout = output_buffer

        if isinstance(__builtins__, dict):
            safe_globals = {"__builtins__": __builtins__}
        else:
            safe_globals = {"__builtins__": __builtins__.__dict__.copy()}

        exec_start = time.perf_counter()
        exec(code, safe_globals, safe_globals)
        exec_end = time.perf_counter()

        output = output_buffer.getvalue()

        print(
            f"[python_worker] execution took {(exec_end - exec_start)*1000:.1f}ms",
            file=sys.stderr
        )

        return {"observation": output, "success": True}

    except Exception as e:
        return {"observation": str(e), "success": False}
    finally:
        sys.stdout = original_stdout
