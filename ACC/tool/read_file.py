"""读取文件工具

该模块提供了读取文件的工具，允许AI读取文本文件内容。
所有文件读取操作都应通过该工具进行，以确保安全性和一致性。
"""

import logging
import os
from typing import Dict, Any

from ACC.tool.base import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)


class ReadFileTool(BaseTool):
    """读取文件工具"""

    def __init__(self):
        """初始化读取文件工具"""
        super().__init__(
            name="read_file", 
            description="读取指定绝对路径的文本文件内容"
        )

    def execute(self, file_path: str) -> Dict[str, Any]:
        """执行读取文件操作

        Args:
            file_path: 文件绝对路径

        Returns:
            执行结果字典，包含文件内容
        """
        try:
            # 直接使用绝对路径
            full_path = os.path.abspath(file_path)

            # 检查文件是否存在
            if not os.path.exists(full_path):
                return {
                    "status": "error",
                    "message": f"文件不存在: {full_path}"
                }

            # 检查是否是文件
            if not os.path.isfile(full_path):
                return {
                    "status": "error",
                    "message": f"不是文件: {full_path}"
                }

            # 读取文件
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            logger.info(f"读取文件成功: {full_path}")

            return {
                "status": "success",
                "message": f"文件读取成功: {full_path}",
                "content": content
            }
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return {
                "status": "error",
                "message": f"读取文件失败: {str(e)}"
            }


# 注册工具
ToolRegistry.register(ReadFileTool())