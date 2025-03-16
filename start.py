#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
总启动脚本
负责初始化环境、清除上次日志并启动Auto-Central-Control系统
"""

import os
import sys
import shutil
import logging
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志格式
def setup_logging(debug=False):
    """设置日志配置"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
    
    # 确保日志目录存在
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 清理旧日志文件
    for file in os.listdir(log_dir):
        file_path = os.path.join(log_dir, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"清理日志文件时出错: {e}")
    
    # 创建新的日志文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"acc_{timestamp}.log")
    
    # 设置日志级别
    log_level = logging.DEBUG if debug else logging.INFO
    
    # 配置日志
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("ACC")

def main(debug=False):
    """主函数，启动系统"""
    # 设置日志
    logger = setup_logging(debug)
    logger.info(f"启动Auto-Central-Control系统，调试模式：{debug}")
    
    try:
        # 导入工作流模块
        from workflow.main import start_workflow
        
        # 启动工作流
        start_workflow(debug)
        
    except Exception as e:
        logger.error(f"系统运行出错: {e}", exc_info=True)
        return 1
    
    logger.info("系统正常退出")
    return 0

if __name__ == "__main__":
    # 如果直接运行此脚本，默认不开启调试模式
    sys.exit(main(debug=False))