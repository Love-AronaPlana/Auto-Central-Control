"""写入文件工具

该模块提供了写入文件的工具，允许AI覆盖文本文件内容。
所有文件写入操作都应通过该工具进行，以确保安全性和一致性。
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any

from ACC.tool.base import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)

# 默认可操作的目录
EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


class WriteFileTool(BaseTool):
    """写入文件工具（支持Windows/Linux）"""

    def __init__(self):
        super().__init__(
            name="write_file",
            description="覆盖写入指定路径的文本文件内容（跨平台支持，自动处理路径差异）",
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            # 参数兼容性处理
            file_path = kwargs.get('file_path') or kwargs.get('path')
            content = kwargs.get('content')

            if not file_path:
                return {
                    "status": "error",
                    "message": "缺少必要参数: file_path/path",
                }
            
            if not content:
                return {
                    "status": "error",
                    "message": "缺少必要参数: content",
                }

            # 使用Path处理路径
            path = Path(file_path).expanduser().resolve()
            
            # 统一路径显示格式
            display_path = str(path.as_posix())

            # Linux/MacOS权限检查
            if os.name != 'nt' and not os.access(path.parent, os.W_OK):
                return {
                    "status": "error",
                    "message": f"无写入权限 ({'请使用sudo' if os.name == 'posix' else '请检查权限'}): {display_path}",
                    "file_path": display_path,
                }

            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件（覆盖模式）
            path.write_text(content, encoding="utf-8")

            logger.info(f"写入文件成功: {display_path}")
            return {
                "status": "success",
                "message": f"文件内容已覆盖写入: {display_path}",
                "file_path": display_path,
            }
        except PermissionError as e:
            error_msg = f"权限不足 ({'请使用管理员权限' if os.name == 'nt' else '请使用sudo'}): {display_path}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            return {
                "status": "error",
                "message": f"写入文件失败: {str(e)}",
                "file_path": display_path,
            }


# 注册工具
ToolRegistry.register(WriteFileTool())
