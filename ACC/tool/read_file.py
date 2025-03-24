"""读取文件工具

该模块提供了读取文件的工具，允许AI读取文本文件内容。
所有文件读取操作都应通过该工具进行，以确保安全性和一致性。
"""

import logging
from pathlib import Path
from typing import Dict, Any

from ACC.tool.base import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)


class ReadFileTool(BaseTool):
    """读取文件工具（支持Windows/Linux）"""

    def __init__(self):
        super().__init__(
            name="read_file",
            description="读取指定路径的文本文件内容（支持Windows/Linux路径格式）"
        )

    def execute(self, file_path: str) -> Dict[str, Any]:
        try:
            # 使用Path处理路径
            path = Path(file_path).expanduser().resolve()
            
            # 统一显示格式
            display_path = str(path.as_posix())

            # 检查文件是否存在
            if not path.exists():
                return {"status": "error", "message": f"文件不存在: {display_path}"}

            # 检查是否是文件
            if not path.is_file():
                return {"status": "error", "message": f"不是文件: {display_path}"}

            # Linux/MacOS权限检查
            if Path('/').exists() and not path.is_file():  # 检查是否为Unix系统
                return {
                    "status": "error",
                    "message": f"无文件读取权限 ({'请使用sudo' if Path('/').exists() else '请检查权限'}): {display_path}"
                }

            # 读取文件
            content = path.read_text(encoding="utf-8")

            logger.info(f"读取文件成功: {display_path}")
            return {
                "status": "success",
                "message": f"文件读取成功: {display_path}",
                "content": content
            }
        except PermissionError as e:
            error_msg = f"权限不足 ({'请使用管理员权限' if not Path('/').exists() else '请使用sudo'}): {display_path}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return {"status": "error", "message": f"读取文件失败: {str(e)}"}


# 注册工具
ToolRegistry.register(ReadFileTool())