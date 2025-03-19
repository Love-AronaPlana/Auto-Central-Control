"""打开文件工具

该模块提供了打开和读取文件的工具，允许AI读取文本文件内容。
所有文件读取操作都应通过该工具进行，以确保安全性和一致性。
"""

import logging
import os
from typing import Dict, Any

from ASN.tool.base import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)

# 默认可操作的目录
EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'examples')

class ReadFileTool(BaseTool):
    """读取文件工具"""
    
    def __init__(self):
        """初始化读取文件工具"""
        super().__init__(
            name="read_file",
            description="读取一个文本文件的内容，文件必须在examples目录或其子目录中"
        )
    
    def execute(self, file_path: str) -> Dict[str, Any]:
        """执行读取文件操作
        
        Args:
            file_path: 文件路径，相对于examples目录
            
        Returns:
            执行结果字典，包含文件内容
        """
        try:
            # 确保文件路径在examples目录下
            if file_path.startswith('/'):
                file_path = file_path[1:]
            
            # 构建完整路径
            full_path = os.path.join(EXAMPLES_DIR, file_path)
            
            # 检查文件是否存在
            if not os.path.exists(full_path):
                return {
                    "status": "error",
                    "message": f"文件不存在: {file_path}"
                }
            
            # 检查是否是文件
            if not os.path.isfile(full_path):
                return {
                    "status": "error",
                    "message": f"不是文件: {file_path}"
                }
            
            # 读取文件
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"读取文件成功: {full_path}")
            
            return {
                "status": "success",
                "message": f"文件读取成功: {file_path}",
                "content": content
            }
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            
            return {
                "status": "error",
                "message": f"读取文件失败: {str(e)}"
            }

class ListDirectoryTool(BaseTool):
    """列出目录内容工具"""
    
    def __init__(self):
        """初始化列出目录内容工具"""
        super().__init__(
            name="list_directory",
            description="列出指定目录中的文件和子目录，目录必须在examples目录或其子目录中"
        )
    
    def execute(self, directory_path: str = "") -> Dict[str, Any]:
        """执行列出目录内容操作
        
        Args:
            directory_path: 目录路径，相对于examples目录，默认为根目录
            
        Returns:
            执行结果字典，包含目录内容列表
        """
        try:
            # 确保目录路径在examples目录下
            if directory_path.startswith('/'):
                directory_path = directory_path[1:]
            
            # 构建完整路径
            full_path = os.path.join(EXAMPLES_DIR, directory_path)
            
            # 检查目录是否存在
            if not os.path.exists(full_path):
                return {
                    "status": "error",
                    "message": f"目录不存在: {directory_path}"
                }
            
            # 检查是否是目录
            if not os.path.isdir(full_path):
                return {
                    "status": "error",
                    "message": f"不是目录: {directory_path}"
                }
            
            # 列出目录内容
            items = os.listdir(full_path)
            files = []
            directories = []
            
            for item in items:
                item_path = os.path.join(full_path, item)
                if os.path.isfile(item_path):
                    files.append(item)
                elif os.path.isdir(item_path):
                    directories.append(item)
            
            logger.info(f"列出目录内容成功: {full_path}")
            
            return {
                "status": "success",
                "message": f"列出目录内容成功: {directory_path}",
                "files": files,
                "directories": directories
            }
        except Exception as e:
            logger.error(f"列出目录内容失败: {e}")
            
            return {
                "status": "error",
                "message": f"列出目录内容失败: {str(e)}"
            }

# 注册工具
ToolRegistry.register(ReadFileTool())
ToolRegistry.register(ListDirectoryTool())
