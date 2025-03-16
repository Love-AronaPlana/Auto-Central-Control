# 日志配置

import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from config.constants import LOG_DIR

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 从环境变量获取日志级别，默认为INFO
log_level_str = os.getenv("LOG_LEVEL", "INFO")
log_level = getattr(logging, log_level_str.upper(), logging.INFO)


# 配置根日志记录器
def configure_logging():
    """配置系统日志"""
    # 保持原有日志格式
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)

    # 创建文件处理器
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "system.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setFormatter(log_format)

    # 获取根日志记录器并配置
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 添加新处理器
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    return root_logger


# 获取指定名称的日志记录器
def get_logger(name):
    """获取指定名称的日志记录器"""
    return logging.getLogger(name)
