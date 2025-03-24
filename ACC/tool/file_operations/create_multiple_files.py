import logging
import os
from pathlib import Path
from typing import Dict, Any, List

from ACC.tool.base import BaseTool, ToolRegistry
from .create_file import CreateFileTool

logger = logging.getLogger(__name__)

class CreateMultipleFilesTool(BaseTool):
    """批量文件创建工具（跨平台支持）"""
    
    def __init__(self):
        super().__init__(
            name="create_multiple_files",
            description="创建多个文本文件（跨平台支持，自动处理路径差异）"
        )

    def execute(self, files: List[Dict[str, str]]) -> Dict[str, Any]:
        results = []
        success_count = 0
        error_count = 0

        for file_info in files:
            # 从文件信息中获取覆盖标志，默认为False
            overwrite = file_info.get("overwrite", False)
            
            result = CreateFileTool().execute(
                file_path=file_info.get("path", ""),
                content=file_info.get("content", ""),
                overwrite=overwrite
            )
            
            # 使用标准化后的路径
            normalized_path = result.get("file_path", file_info.get("path"))
            
            # 使用 Path 处理路径，确保跨平台兼容性
            path = Path(normalized_path)
            display_path = str(path.as_posix())  # 统一使用正斜杠
            
            results.append({
                "file_path": display_path,
                "status": result.get("status"),
                "message": result.get("message"),
                "error_type": result.get("error_type")
            })
            
            if result.get("status") == "success":
                success_count += 1
            else:
                error_count += 1

        return {
            "status": "success" if error_count == 0 else "partial_success",
            "message": f"创建完成: {success_count}成功/{error_count}失败",
            "results": results,
            "platform": os.name  # 返回当前操作系统类型
        }

# 注册工具
ToolRegistry.register(CreateMultipleFilesTool())