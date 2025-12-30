import sys
from datetime import datetime

from loguru import logger as _logger

from app.config import PROJECT_ROOT


_print_level = "WARNING"


def define_log_level(print_level="INFO", logfile_level="DEBUG", name: str = None):
    """Adjust the log level to above level

    日志策略：
    - 按日期分割日志文件（每天一个文件）
    - 同一天的任务追加到同一个文件
    - 保留最近 7 天的日志
    - 单个文件超过 50MB 时轮转
    """
    global _print_level
    _print_level = print_level

    current_date = datetime.now()
    # 使用日期（而非精确到秒）作为文件名，同一天的日志追加到同一文件
    formatted_date = current_date.strftime("%Y%m%d")
    log_name = f"{name}_{formatted_date}" if name else formatted_date

    _logger.remove()
    _logger.add(sys.stderr, level=print_level)
    _logger.add(
        PROJECT_ROOT / f"logs/{log_name}.log",
        level=logfile_level,
        rotation="50 MB",      # 单文件超过 50MB 时轮转
        retention="7 days",    # 保留最近 7 天的日志
        encoding="utf-8",
        enqueue=True,          # 异步写入，避免阻塞
        backtrace=True,        # 记录完整的异常堆栈
        diagnose=True,         # 记录变量值，便于调试
    )
    return _logger


logger = define_log_level()


if __name__ == "__main__":
    logger.info("Starting application")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
