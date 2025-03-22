"""写入文件工具

该模块提供了写入文件的工具，允许AI覆盖文本文件内容。
所有文件写入操作都应通过该工具进行，以确保安全性和一致性。
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


class WriteFileTool(BaseTool):
    """写入文件工具"""

    def __init__(self):
        """初始化写入文件工具"""
        super().__init__(
            name="write_file",
            description="覆盖写入指定绝对路径的文本文件内容（警告：将覆盖文件的所有现有内容）",  # 修改描述
        )

    def execute(self, file_path: str, content: str) -> Dict[str, Any]:
        """执行写入文件操作

        Args:
            file_path: 文件绝对路径  # 参数说明修改
            content: 要写入的文件内容（将覆盖原有内容）

        Returns:
            执行结果字典
        """
        try:
            # 直接使用绝对路径（移除路径处理逻辑）
            full_path = os.path.abspath(file_path)

            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # 写入文件（覆盖模式）
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"写入文件成功: {full_path}")

            return {
                "status": "success",
                "message": f"文件内容已覆盖写入: {full_path}",  # 返回绝对路径
                "file_path": full_path,  # 返回绝对路径
            }
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            return {
                "status": "error",
                "message": f"写入文件失败: {str(e)}",
                "file_path": full_path,  # 返回绝对路径
            }


# 注册工具
ToolRegistry.register(WriteFileTool())
