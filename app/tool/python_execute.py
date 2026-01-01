import atexit
import time
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import ClassVar, Dict, Optional

from loguru import logger

from app.tool.base import BaseTool
from app.workers.python_worker import execute_code as _worker_execute_code


class PythonExecute(BaseTool):
    """
    A tool for executing Python code with timeout and safety restrictions.
    Uses a process pool to avoid repeated module initialization overhead.
    """

    name: str = "python_execute"
    description: str = (
        "Executes Python code string. Note: Only print outputs are visible, "
        "function return values are not captured. Use print statements to see results."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python code to execute.",
            },
        },
        "required": ["code"],
    }

    # 类级别的进程池（所有实例共享）
    _executor: ClassVar[Optional[ProcessPoolExecutor]] = None
    _pool_size: ClassVar[int] = 2  # 默认池大小
    _initialized: ClassVar[bool] = False

    @classmethod
    def _get_executor(cls) -> ProcessPoolExecutor:
        """获取或创建进程池（懒加载 + 单例模式）"""
        if cls._executor is None:
            logger.info(
                f"⏱️ [python_execute] Creating process pool with {cls._pool_size} workers..."
            )
            pool_start = time.perf_counter()

            cls._executor = ProcessPoolExecutor(max_workers=cls._pool_size)

            # 注册退出时清理
            atexit.register(cls._shutdown_executor)

            pool_ready = time.perf_counter()
            logger.info(
                f"⏱️ [python_execute] Process pool created in "
                f"{(pool_ready - pool_start)*1000:.1f}ms"
            )
            cls._initialized = True

        return cls._executor

    @classmethod
    def _shutdown_executor(cls) -> None:
        """关闭进程池"""
        if cls._executor is not None:
            logger.info("⏱️ [python_execute] Shutting down process pool...")
            cls._executor.shutdown(wait=False)
            cls._executor = None
            cls._initialized = False

    async def execute(
        self,
        code: str,
        timeout: int = 30,
    ) -> Dict:
        """
        Executes the provided Python code with a timeout.
        Uses a process pool to avoid repeated module initialization.

        Args:
            code (str): The Python code to execute.
            timeout (int): Execution timeout in seconds.

        Returns:
            Dict: Contains 'observation' with execution output and 'success' status.
        """
        total_start = time.perf_counter()
        logger.info("⏱️ [python_execute] Starting execution (pool mode)...")

        try:
            # 获取进程池
            executor = self._get_executor()

            # 提交任务到进程池
            submit_time = time.perf_counter()
            future = executor.submit(_worker_execute_code, code, submit_time)

            logger.info(
                f"⏱️ [python_execute] Task submitted in "
                f"{(time.perf_counter() - submit_time)*1000:.1f}ms"
            )

            # 等待结果（带超时）
            result = future.result(timeout=timeout)

            total_time = time.perf_counter() - total_start
            logger.info(
                f"⏱️ [python_execute] Total execution time: {total_time*1000:.1f}ms"
            )
            return result

        except FuturesTimeoutError:
            total_time = time.perf_counter() - total_start
            logger.warning(f"⏱️ [python_execute] TIMEOUT after {total_time*1000:.1f}ms")
            return {
                "observation": f"Execution timeout after {timeout} seconds",
                "success": False,
            }
        except Exception as e:
            logger.error(f"⏱️ [python_execute] Error: {e}")
            return {
                "observation": f"Execution error: {str(e)}",
                "success": False,
            }
