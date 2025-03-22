"""删除文件工具

该模块提供了删除文件的工具，允许AI删除文本文件。
所有文件删除操作都应通过该工具进行，以确保安全性和一致性。
"""

import logging
import os
from typing import Dict, Any, List

from ACC.tool.base import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)

# 移除 EXAMPLES_DIR 常量定义


class DeleteFileTool(BaseTool):
    """删除文件工具"""

    def __init__(self):
        """初始化删除文件工具"""
        super().__init__(
            name="delete_file",
            description="删除一个文本文件（支持绝对路径操作）",  # 修改描述
        )

    def execute(self, file_path: str) -> Dict[str, Any]:
        """执行删除文件操作

        Args:
            file_path: 文件绝对路径  # 参数说明修改

        Returns:
            执行结果字典
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

            # 删除文件
            os.remove(full_path)

            logger.info(f"删除文件成功: {full_path}")

            return {
                "status": "success",
                "message": f"文件删除成功: {full_path}",  # 返回绝对路径
            }
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return {"status": "error", "message": f"删除文件失败: {str(e)}"}


class DeleteMultipleFilesTool(BaseTool):
    """删除多个文件工具"""

    def __init__(self):
        """初始化删除多个文件工具"""
        super().__init__(
            name="delete_multiple_files",
            description="删除多个文本文件（支持绝对路径操作）",  # 修改描述
        )

    def execute(self, file_paths: List[str]) -> Dict[str, Any]:
        """执行删除多个文件操作

        Args:
            file_paths: 文件绝对路径列表  # 参数说明修改

        Returns:
            执行结果字典
        """
        results = []
        success_count = 0
        error_count = 0

        for file_path in file_paths:
            delete_tool = DeleteFileTool()
            result = delete_tool.execute(file_path)

            results.append(result)

            if result["status"] == "success":
                success_count += 1
            else:
                error_count += 1

        return {
            "status": "completed",
            "message": f"删除操作完成，成功: {success_count}，失败: {error_count}",
            "results": results,
        }


# 注册工具
ToolRegistry.register(DeleteFileTool())
ToolRegistry.register(DeleteMultipleFilesTool())
