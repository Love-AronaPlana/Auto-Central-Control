"""配置模块，负责读取和管理配置信息

该模块提供了读取配置文件的功能，所有需要使用配置信息的模块都应通过该模块获取。
配置文件路径为config/config.toml，包含API设置、模型选择等信息。
"""

import os
import logging
from typing import Dict, Any, Optional

import toml

logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'config.toml')

# 缓存配置信息
_config_cache = None

def get_config(reload: bool = False) -> Dict[str, Any]:
    """获取配置信息
    
    Args:
        reload: 是否重新加载配置文件，默认为False
        
    Returns:
        配置信息字典
    """
    global _config_cache
    
    if _config_cache is None or reload:
        try:
            if not os.path.exists(CONFIG_PATH):
                logger.error(f"配置文件不存在: {CONFIG_PATH}")
                raise FileNotFoundError(f"配置文件不存在: {CONFIG_PATH}")
                
            _config_cache = toml.load(CONFIG_PATH)
            logger.info(f"成功加载配置文件: {CONFIG_PATH}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    return _config_cache

def get_llm_config() -> Dict[str, Any]:
    """获取LLM配置信息
    
    Returns:
        LLM配置信息字典
    """
    config = get_config()
    return config.get('llm', {})
