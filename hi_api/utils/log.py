from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, level="INFO", format="[{time:YYYY-MM-DD HH:mm:ss}] [{level}] {message}")

# 可选：写入文件
# logger.add("logs/hi_api_{time:YYYYMMDD}.log", rotation="1 day", retention="7 days", level="DEBUG")

def get_logger(name: str = None):
    if name:
        return logger.bind(module=name)
    return logger
