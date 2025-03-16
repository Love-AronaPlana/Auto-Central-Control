#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
workflow/config.py - 工作流配置模块

该模块负责管理工作流的配置信息和参数。
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# 默认配置
DEFAULT_CONFIG = {
    # 模型配置
    "model": {
        "name": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    },
    # 工作流配置
    "workflow": {
        "max_steps": 10,  # 最大步骤数
        "max_fix_attempts": 3,  # 最大修复尝试次数
        "auto_save": True,  # 是否自动保存执行结果
        "save_path": "./results",  # 结果保存路径
    },
    # 日志配置
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s\n%(message)s",  # 添加换行符
        "file": "./log/workflow.log",
    },
    # 工具配置
    "tools": {"text_analyzer": {"enabled": True, "max_keywords": 10}},
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    # 从环境变量加载目录限制配置
    allowed_paths = os.getenv("ALLOWED_PATHS", "./workspace").split(",")
    allow_outside = os.getenv("ALLOW_OUTSIDE_WORKSPACE", "false").lower() == "true"

    return {
        "directory_restrictions": {
            "allowed_paths": [path.strip() for path in allowed_paths],
            "allow_outside_workspace": allow_outside,
        },
        "model": {
            "name": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
        # 工作流配置
        "workflow": {
            "max_steps": 10,  # 最大步骤数
            "max_fix_attempts": 3,  # 最大修复尝试次数
            "auto_save": True,  # 是否自动保存执行结果
            "save_path": "./results",  # 结果保存路径
        },
        # 日志配置
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "./log/workflow.log",
        },
        # 工具配置
        "tools": {"text_analyzer": {"enabled": True, "max_keywords": 10}},
    }

    config = DEFAULT_CONFIG.copy()

    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)

            # 合并用户配置和默认配置
            _merge_config(config, user_config)
            logging.info(f"已从 {config_path} 加载配置")
        except Exception as e:
            logging.error(f"加载配置文件失败: {str(e)}")
    else:
        logging.info("使用默认配置")

    return config


def _merge_config(default_config: Dict[str, Any], user_config: Dict[str, Any]) -> None:
    """
    合并配置

    Args:
        default_config: 默认配置
        user_config: 用户配置
    """
    for key, value in user_config.items():
        if (
            key in default_config
            and isinstance(default_config[key], dict)
            and isinstance(value, dict)
        ):
            _merge_config(default_config[key], value)
        else:
            default_config[key] = value


def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """
    保存配置到文件

    Args:
        config: 配置信息
        config_path: 配置文件路径

    Returns:
        bool: 是否保存成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logging.info(f"配置已保存到 {config_path}")
        return True
    except Exception as e:
        logging.error(f"保存配置失败: {str(e)}")
        return False


def get_model_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取模型配置

    Args:
        config: 完整配置

    Returns:
        Dict[str, Any]: 模型配置
    """
    return config.get("model", DEFAULT_CONFIG["model"])


def get_workflow_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取工作流配置

    Args:
        config: 完整配置

    Returns:
        Dict[str, Any]: 工作流配置
    """
    return config.get("workflow", DEFAULT_CONFIG["workflow"])


def get_logging_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取日志配置（更新后）
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "[%(asctime)s] [%(module)s]\n%(message)s",  # 添加换行符
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "debug": {
                "format": "[%(asctime)s] [%(module)s:%(funcName)s] [%(levelname)s]\n%(message)s",  # 添加换行符
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            # ... 保持现有handler配置不变 ...
        },
    }


def get_tool_config(config: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
    """
    获取指定工具的配置

    Args:
        config: 完整配置
        tool_name: 工具名称

    Returns:
        Dict[str, Any]: 工具配置，如果工具不存在则返回空字典
    """
    tools_config = config.get("tools", {})
    return tools_config.get(tool_name, {})


if __name__ == "__main__":
    # 测试代码
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if len(sys.argv) > 1:
        config = load_config(sys.argv[1])
    else:
        config = load_config()

    print(json.dumps(config, indent=2, ensure_ascii=False))
