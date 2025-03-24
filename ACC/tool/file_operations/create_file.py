import logging
from pathlib import Path
from typing import Dict, Any

from ACC.tool.base import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)

class CreateFileTool(BaseTool):
    """创建跨平台文件工具"""
    
    def __init__(self):
        super().__init__(
            name="create_file",
            description="创建新的文本文件（跨平台支持，自动处理路径差异）"
        )

    def execute(self, file_path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
        try:
            # 使用Path处理路径
            path = Path(file_path).expanduser().resolve()
            
            # 创建父目录
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # 统一显示格式（使用forward slashes）
            display_path = str(path).replace('\\', '/')
            
            if path.exists() and not overwrite:
                return {
                    "status": "error",
                    "message": f"文件已存在: {display_path}",
                    "error_type": "file_exists",
                    "file_path": display_path,
                }

            # 通用文件写入（已处理编码）
            path.write_text(content, encoding="utf-8")

            # Linux权限处理
            if Path('/').exists() and not path.parent.is_dir():  # 检查是否为Unix系统
                return {
                    "status": "error",
                    "message": f"权限不足，请使用sudo执行: {display_path}",
                    "error_type": "permission_denied",
                    "file_path": display_path,
                }

            logger.info(f"创建文件成功: {display_path}")
            return {"status": "success", "message": f"文件创建成功: {display_path}"}
            
        except PermissionError as e:
            logger.error(f"权限错误: {e}")
            return {
                "status": "error",
                "message": f"权限不足 ({'请使用管理员权限' if Path('C:/').exists() else '请使用sudo'}): {str(e)}",
                "error_type": "permission_denied",
                "file_path": display_path,
            }
        except OSError as e:
            logger.error(f"系统错误: {e}")
            return {
                "status": "error",
                "message": f"系统错误: {str(e)}",
                "error_type": "os_error",
                "file_path": display_path,
            }
        except Exception as e:
            logger.error(f"创建文件失败: {e}")
            return {"status": "error", "message": f"创建文件失败: {str(e)}"}

# 注册工具
ToolRegistry.register(CreateFileTool())