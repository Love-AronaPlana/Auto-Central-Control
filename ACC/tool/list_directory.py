"""目录列表工具

该模块提供了列出目录内容的工具，允许AI获取目录中的文件和子目录列表。
所有目录列表操作都应通过该工具进行，以确保安全性和一致性。
"""

import logging
import os
from pathlib import Path  # 添加 Path 导入
from typing import Dict, Any

from ACC.tool.base import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)


class ListDirectoryTool(BaseTool):
    """列出目录内容工具"""

    def __init__(self):
        super().__init__(
            name="list_directory", 
            description="列出指定绝对路径的目录内容"
        )

    def execute(self, path: str) -> Dict[str, Any]:
        """执行列出目录内容操作（支持Windows/Linux）
        
        Args:
            path: 支持以下格式：
                - Windows绝对路径 (C:\\Users\\user)
                - Linux绝对路径 (/home/user)
                - 网络路径 (\\\\server\\share)
                - 支持 ~ 扩展用户目录
        """
        try:
            # 使用 Path 处理路径
            path_obj = Path(path).expanduser().resolve()
            
            # 检查路径是否存在
            if not path_obj.exists():
                return {"status": "error", "message": f"路径不存在: {path_obj}"}

            # 检查是否是目录
            if not path_obj.is_dir():
                return {"status": "error", "message": f"不是目录: {path_obj}"}

            # 检查目录访问权限 (Linux/MacOS)
            if os.name != 'nt' and not os.access(path_obj, os.R_OK):
                return {"status": "error", "message": f"无目录访问权限: {path_obj}"}

            files = []
            directories = []
            hidden_files = []
            hidden_dirs = []

            for item in path_obj.iterdir():
                # 跨平台隐藏文件判断
                if os.name == 'nt':
                    is_hidden = bool(item.stat().st_file_attributes & 2)  # FILE_ATTRIBUTE_HIDDEN
                else:
                    is_hidden = item.name.startswith('.')
                
                entry = {
                    "name": item.name,
                    "absolute_path": str(item),
                    "is_hidden": is_hidden
                }

                if item.is_file():
                    (hidden_files if is_hidden else files).append(entry)
                elif item.is_dir():
                    (hidden_dirs if is_hidden else directories).append(entry)

            logger.info(f"列出目录成功: {path_obj}")
            return {
                "status": "success",
                "path": str(path_obj),
                "files": files,
                "directories": directories,
                "hidden_files": hidden_files,
                "hidden_directories": hidden_dirs,
                "platform": os.name
            }
        except Exception as e:
            logger.error(f"目录列表错误: {str(e)}")
            return {
                "status": "error",
                "message": f"目录列表失败: {str(e)}",
                "platform": os.name
            }


# 注册工具
ToolRegistry.register(ListDirectoryTool())