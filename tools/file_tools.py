# 文件操作工具

import os
import json
from config.logging_config import get_logger
from config.constants import WORKSPACE_DIR

# 获取日志记录器
logger = get_logger(__name__)

# 确保工作空间目录存在
os.makedirs(WORKSPACE_DIR, exist_ok=True)


def file_read(file_path, start_line=None, end_line=None):
    """读取文件内容
    
    Args:
        file_path (str): 文件路径，如果是相对路径，则相对于工作空间目录
        start_line (int, optional): 开始行号（从0开始）
        end_line (int, optional): 结束行号（不包含该行）
        
    Returns:
        dict: 包含状态和内容的字典
    """
    try:
        # 处理相对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(WORKSPACE_DIR, file_path)
            
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return {
                "status": "error",
                "message": f"文件不存在: {file_path}"
            }
            
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # 处理行范围
        if start_line is not None and end_line is not None:
            start_line = max(0, start_line)
            end_line = min(len(lines), end_line)
            content = ''.join(lines[start_line:end_line])
        else:
            content = ''.join(lines)
            
        logger.info(f"成功读取文件: {file_path}")
        return {
            "status": "success",
            "content": content
        }
        
    except Exception as e:
        logger.error(f"读取文件时出错: {str(e)}")
        return {
            "status": "error",
            "message": f"读取文件时出错: {str(e)}"
        }


def file_write(file_path, content, append=False):
    """写入内容到文件
    
    Args:
        file_path (str): 文件路径，如果是相对路径，则相对于工作空间目录
        content (str): 要写入的内容
        append (bool, optional): 是否追加模式，默认为False（覆盖模式）
        
    Returns:
        dict: 包含状态和消息的字典
    """
    try:
        # 处理相对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(WORKSPACE_DIR, file_path)
            
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
        # 写入文件
        mode = 'a' if append else 'w'
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"成功{'追加' if append else '写入'}内容到文件: {file_path}")
        return {
            "status": "success",
            "message": f"成功{'追加' if append else '写入'}内容到文件"
        }
        
    except Exception as e:
        logger.error(f"写入文件时出错: {str(e)}")
        return {
            "status": "error",
            "message": f"写入文件时出错: {str(e)}"
        }