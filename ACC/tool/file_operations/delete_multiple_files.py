import logging
from typing import Dict, Any, List
from pathlib import Path

from ACC.tool.base import BaseTool, ToolRegistry
from .delete_file import DeleteFileTool

logger = logging.getLogger(__name__)

class DeleteMultipleFilesTool(BaseTool):
    """跨平台批量文件删除工具"""
    
    def __init__(self):
        super().__init__(
            name="delete_multiple_files",
            description="跨平台批量删除文件（支持Windows/Linux路径规范）"
        )

    def execute(self, file_paths: List[str]) -> Dict[str, Any]:
        results = []
        success_count = 0
        error_count = 0

        for raw_path in file_paths:
            try:
                # 使用 Path 统一处理路径
                path = Path(raw_path).expanduser().resolve()
                
                # 统一路径显示格式（使用正斜杠）
                display_path = str(path.as_posix())
                
                # 执行删除操作
                result = DeleteFileTool().execute(str(path))
                result["file_path"] = display_path  # 返回标准化后的显示路径
            except Exception as e:
                result = {
                    "status": "error",
                    "message": f"路径处理失败: {str(e)}",
                    "file_path": raw_path
                }
            
            results.append(result)
            if result["status"] == "success":
                success_count += 1
            else:
                error_count += 1

        return {
            "status": "completed",
            "message": f"删除完成: {success_count}成功/{error_count}失败",
            "results": results,
            "platform": Path().absolute().drive and "nt" or "posix"  # 更准确的平台判断
        }

ToolRegistry.register(DeleteMultipleFilesTool())