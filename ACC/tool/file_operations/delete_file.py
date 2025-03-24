import logging
import stat
from pathlib import Path
from typing import Dict, Any

from ACC.tool.base import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)

class DeleteFileTool(BaseTool):
    """跨平台文件删除工具"""
    
    def __init__(self):
        super().__init__(
            name="delete_file",
            description="删除指定路径的文本文件（支持Windows/Linux跨平台操作）"
        )

    def execute(self, file_path: str) -> Dict[str, Any]:
        try:
            # 使用Path处理路径
            path = Path(file_path).expanduser().resolve()
            
            # 统一显示格式（使用forward slashes）
            display_path = str(path).replace('\\', '/')

            if not path.exists():
                return {"status": "error", "message": f"文件不存在: {display_path}"}
            if not path.is_file():
                return {"status": "error", "message": f"不是文件: {display_path}"}

            # Windows下处理只读属性
            if Path('C:/').exists():  # Windows系统检查
                path.chmod(path.stat().st_mode | stat.S_IWRITE)
                
            path.unlink()  # 删除文件
            logger.info(f"删除文件成功: {display_path}")
            return {"status": "success", "message": f"文件删除成功: {display_path}"}
            
        except PermissionError as e:
            error_msg = f"权限不足 ({'请使用管理员权限' if Path('C:/').exists() else '请使用sudo'}): {display_path}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return {"status": "error", "message": f"删除文件失败: {str(e)}"}

ToolRegistry.register(DeleteFileTool())