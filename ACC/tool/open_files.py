"""打开文件工具

该模块提供了打开和读取文件的工具，允许AI读取文本文件内容。
所有文件读取操作都应通过该工具进行，以确保安全性和一致性。
"""

import logging
import os
from typing import Dict, Any

from ACC.tool.base import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)

# 默认可操作的目录
EXAMPLES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "examples",
)

# 移除 EXAMPLES_DIR 常量定义


class ReadFileTool(BaseTool):
    """读取文件工具"""

    def __init__(self):
        """初始化读取文件工具"""
        super().__init__(
            name="read_file", description="读取指定绝对路径的文本文件内容"  # 修改描述
        )

    def execute(self, file_path: str) -> Dict[str, Any]:
        """执行读取文件操作

        Args:
            file_path: 文件绝对路径  # 参数说明修改

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
                    "message": f"文件不存在: {full_path}",  # 返回绝对路径
                }

            # 检查是否是文件
            if not os.path.isfile(full_path):
                return {
                    "status": "error",
                    "message": f"不是文件: {full_path}",  # 返回绝对路径
                }

            # 读取文件（后续代码保持不变）
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            logger.info(f"读取文件成功: {full_path}")

            return {
                "status": "success",
                "message": f"文件读取成功: {full_path}",  # 返回绝对路径
                "content": content,
            }
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return {"status": "error", "message": f"读取文件失败: {str(e)}"}


class ListDirectoryTool(BaseTool):
    """列出目录内容工具"""

    def __init__(self):
        """初始化列出目录内容工具"""
        super().__init__(
            name="list_directory", description="列出指定绝对路径的目录内容"  # 修改描述
        )

    def execute(self, directory_path: str) -> Dict[str, Any]:  # 移除默认值
        """执行列出目录内容操作

        Args:
            directory_path: 目录绝对路径  # 参数说明修改

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
                    "message": f"目录不存在: {full_path}",  # 返回绝对路径
                }

            # 检查是否是目录
            if not os.path.isdir(full_path):
                return {
                    "status": "error",
                    "message": f"不是目录: {full_path}",  # 返回绝对路径
                }

            # 列出目录内容（后续代码保持不变）
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
                "message": f"列出目录内容成功: {full_path}",  # 返回绝对路径
                "files": files,
                "directories": directories,
            }
        except Exception as e:
            logger.error(f"列出目录内容失败: {e}")
            return {"status": "error", "message": f"列出目录内容失败: {str(e)}"}


# 注册工具
ToolRegistry.register(ReadFileTool())
ToolRegistry.register(ListDirectoryTool())
