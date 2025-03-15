#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
start.py - 总启动脚本

该脚本是Auto-Central-Control系统的主入口，负责初始化系统环境、清除上次日志并启动工作流程。
"""

import os
import sys
import shutil
import logging
from datetime import datetime
from dotenv import load_dotenv


# 确保所有必要的目录存在
def ensure_directories():
    """
    确保所有必要的目录结构存在，如果不存在则创建
    """
    directories = [
        "agent",
        "agent/prompts",
        "actions",
        "config",
        "workplace",
        "memory",
        "workflow",
        "plugins",
        "tools",
        "log",
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"创建目录: {directory}")


# 初始化日志系统
def init_logging():
    """
    初始化日志系统，配置日志格式和级别
    """
    log_dir = "log"

    # 清除旧日志文件
    if os.path.exists(log_dir):
        for file in os.listdir(log_dir):
            if file.endswith(".log"):
                os.remove(os.path.join(log_dir, file))
    else:
        os.makedirs(log_dir)

    # 创建新的日志文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"acc_{timestamp}.log")

    # 配置日志级别
    # 从环境变量获取日志级别，默认INFO
    log_level = os.getenv("LOG_LEVEL", "INFO")  # 默认值已内置在代码中
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # 从环境变量获取调试模式，默认false
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    logging.info("日志系统初始化完成")
    return logging.getLogger("ACC")


# 加载配置
def load_config():
    """
    加载系统配置
    """
    load_dotenv()

    # 检查必要的环境变量
    required_vars = ["API_URL", "API_KEY", "MODEL_NAME", "MAX_TOKENS"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"错误: 缺少必要的环境变量: {', '.join(missing_vars)}")
        print("请检查.env文件配置")
        sys.exit(1)

    # 获取DEBUG模式设置
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"

    return {
        "api_url": os.getenv("API_URL"),
        "api_key": os.getenv("API_KEY"),
        "model_name": os.getenv("MODEL_NAME"),
        "max_tokens": int(os.getenv("MAX_TOKENS")),
        "debug": debug_mode,
    }


# 主函数
def main():
    """
    系统主入口函数
    """
    # 确保目录结构
    ensure_directories()

    # 初始化日志
    logger = init_logging()

    # 加载配置
    config = load_config()

    logger.info("Auto-Central-Control 系统启动")
    logger.info(f"使用模型: {config['model_name']}")
    logger.info(f"DEBUG模式: {'开启' if config['debug'] else '关闭'}")

    try:
        # 导入并启动工作流
        from workflow.main import start_workflow

        start_workflow(config, logger)
    except Exception as e:
        logger.error(f"系统运行出错: {str(e)}", exc_info=True)
        print(f"系统运行出错: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
