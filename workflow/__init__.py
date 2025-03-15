#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
workflow/__init__.py - 工作流模块初始化

该模块负责初始化工作流环境和加载配置。
"""

import os
import logging
from typing import Dict, Any

# 导入工作流模块
from .config import load_config, get_logging_config
from .executor import WorkflowExecutor, execute_workflow
from .self_check import run_self_check

# 初始化日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('workflow')

# 工作流版本信息
__version__ = '1.0.0'

def initialize(config_path=None) -> Dict[str, Any]:
    """
    初始化工作流环境
    
    Args:
        config_path: 配置文件路径，如果为None则使用默认配置
        
    Returns:
        Dict[str, Any]: 初始化结果
    """
    logger.info(f"初始化工作流环境，版本: {__version__}")
    
    # 加载配置
    config = load_config(config_path)
    
    # 配置日志
    log_config = get_logging_config(config)
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = log_config.get('file')
    
    if log_file:
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        # 配置文件日志
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
    
    logger.setLevel(log_level)
    
    # 运行自检查
    check_result = run_self_check(logger)
    
    return {
        'status': 'success' if check_result['status'] == 'success' else 'warning',
        'config': config,
        'check_result': check_result,
        'version': __version__
    }