"""创建文件工具

该模块提供了创建文件的工具，允许AI创建文本文件。
所有文件创建操作都应通过该工具进行，以确保安全性和一致性。
"""

import logging
import os
from typing import Dict, Any, List

from ASN.tool.base import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)

# 默认可操作的目录
EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'examples')

class CreateFileTool(BaseTool):
    """创建文件工具"""
    
    def __init__(self):
        """初始化创建文件工具"""
        super().__init__(
            name="create_file",
            description="创建一个文本文件，文件必须在examples目录或其子目录中"
        )
    
    def execute(self, file_path: str, content: str) -> Dict[str, Any]:
        """执行创建文件操作
        
        Args:
            file_path: 文件路径，相对于examples目录
            content: 文件内容
            
        Returns:
            执行结果字典
        """
        try:
            # 确保文件路径在examples目录下
            if file_path.startswith('/'):
                file_path = file_path[1:]
            
            # 构建完整路径
            full_path = os.path.join(EXAMPLES_DIR, file_path)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 检查文件是否已存在
            if os.path.exists(full_path):
                return {
                    "status": "error",
                    "message": f"文件已存在: {file_path}"
                }
            
            # 创建文件
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"创建文件成功: {full_path}")
            
            return {
                "status": "success",
                "message": f"文件创建成功: {file_path}"
            }
        except Exception as e:
            logger.error(f"创建文件失败: {e}")
            
            return {
                "status": "error",
                "message": f"创建文件失败: {str(e)}"
            }

class CreateMultipleFilesTool(BaseTool):
    """创建多个文件工具"""
    
    def __init__(self):
        """初始化创建多个文件工具"""
        super().__init__(
            name="create_multiple_files",
            description="创建多个文本文件，文件必须在examples目录或其子目录中"
        )
    
    def execute(self, files: List[Dict[str, str]]) -> Dict[str, Any]:
        """执行创建多个文件操作
        
        Args:
            files: 文件列表，每个文件包含路径和内容
            
        Returns:
            执行结果字典
        """
        results = []
        success_count = 0
        error_count = 0
        
        for file_info in files:
            file_path = file_info.get('path', '')
            content = file_info.get('content', '')
            
            create_tool = CreateFileTool()
            result = create_tool.execute(file_path, content)
            
            results.append({
                "file_path": file_path,
                "status": result.get("status"),
                "message": result.get("message")
            })
            
            if result.get("status") == "success":
                success_count += 1
            else:
                error_count += 1
        
        return {
            "status": "success" if error_count == 0 else "partial_success" if success_count > 0 else "error",
            "message": f"创建文件完成: {success_count}个成功, {error_count}个失败",
            "results": results
        }

# 注册工具
ToolRegistry.register(CreateFileTool())
ToolRegistry.register(CreateMultipleFilesTool())
