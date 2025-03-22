"""目录列表工具

该模块提供了列出目录内容的工具，允许AI获取目录中的文件和子目录列表。
所有目录列表操作都应通过该工具进行，以确保安全性和一致性。
"""

import logging
import os
from typing import Dict, Any

from ACC.tool.base import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)


class ListDirectoryTool(BaseTool):
    """列出目录内容工具"""

    def __init__(self):
        """初始化列出目录内容工具"""
        super().__init__(
            name="list_directory", 
            description="列出指定绝对路径的目录内容"
        )

    def execute(self, directory_path: str) -> Dict[str, Any]:
        """执行列出目录内容操作

        Args:
            directory_path: 目录绝对路径

        Returns:
            执行结果字典，包含目录内容列表
        """
        try:
            # 处理为绝对路径
            full_path = os.path.abspath(directory_path)

            # 检查目录是否存在
            if not os.path.exists(full_path):
                return {
                    "status": "error",
                    "message": f"目录不存在: {full_path}"
                }

            # 检查是否是目录
            if not os.path.isdir(full_path):
                return {
                    "status": "error",
                    "message": f"不是目录: {full_path}"
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
                "message": f"列出目录内容成功: {full_path}",
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
ToolRegistry.register(ListDirectoryTool())