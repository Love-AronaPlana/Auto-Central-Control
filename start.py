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
    directories = [
        "workspace",  # 新增必须的workspace目录
        "agent",
        "agent/prompts",
        "actions",
        "config",
        "workspace",
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
    # 应添加缺失的环境变量检查
    required_log_vars = [
        "CLEAN_LOG_ON_START",
        "CLEAN_MEMORY_ON_START",
        "MEMORY_RETENTION_COUNT",
    ]
    missing_log_vars = [var for var in required_log_vars if not os.getenv(var)]
    if missing_log_vars:
        print(f"缺少日志相关环境变量: {', '.join(missing_log_vars)}")
        sys.exit(1)

    """
    初始化日志系统，配置日志格式和级别
    """
    log_dir = "log"

    # 新增清理判断逻辑
    if os.getenv("CLEAN_LOG_ON_START", "true").lower() == "true":
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                if file.endswith(".log"):
                    os.remove(os.path.join(log_dir, file))
        else:
            os.makedirs(log_dir)
    else:
        os.makedirs(log_dir, exist_ok=True)

    # 新增内存清理逻辑
    if os.getenv("CLEAN_MEMORY_ON_START", "true").lower() == "true":
        memory_dir = "memory"
        if os.path.exists(memory_dir):
            # 从环境变量获取保留数量，默认5
            try:
                retention = int(os.getenv("MEMORY_RETENTION_COUNT", "5"))
            except ValueError:
                retention = 5
                logging.warning(
                    f"MEMORY_RETENTION_COUNT配置无效，使用默认值{retention}"
                )

            # 获取所有 memory 文件并按时间排序
            memory_files = sorted(
                [f for f in os.listdir(memory_dir) if f.startswith("conversation_")],
                key=lambda x: os.path.getmtime(os.path.join(memory_dir, x)),
                reverse=True,
            )

            # 保留指定数量的文件
            for f in memory_files[retention:]:
                os.remove(os.path.join(memory_dir, f))
                print(f"清理旧内存文件: {f} (保留最新 {retention} 个)")

    # 创建新的日志文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"acc_{timestamp}.log")

    # 修复日志级别设置逻辑
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "DEBUG" if debug_mode else "INFO")  # 修改点

    numeric_level = getattr(
        logging, log_level.upper(), logging.DEBUG if debug_mode else logging.INFO
    )

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    # 添加JSON美化配置
    logging.getLogger().handlers[0].formatter = logging.Formatter(
        "[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    logging.info("日志系统初始化完成")
    return logging.getLogger("ACC")


# 加载配置
def load_config():
    if not os.path.exists(".env"):
        # 自动复制示例文件
        shutil.copy(".env.example", ".env")
        print("检测到缺少.env文件，已自动创建示例配置")
        print("请修改.env文件中的配置后重新启动ACC")
        sys.exit(0)

    load_dotenv()  # 直接加载.env文件，不会自动创建
    # 检查必要变量但不会自动创建文件
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
