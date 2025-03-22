"""系统信息工具

该模块提供了获取系统信息的工具，包括用户信息和系统路径等。
"""

import os
import logging
import getpass
from pathlib import Path
from typing import Dict, Any

from ACC.tool.base import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)

class SystemInfoTool(BaseTool):
    """系统信息工具"""

    def __init__(self):
        """初始化系统信息工具"""
        super().__init__(
            name="system_info",
            description="获取系统信息，包括用户名、桌面路径等系统路径"
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行获取系统信息操作

        Returns:
            执行结果字典，包含系统信息
        """
        try:
            # 获取用户信息
            username = getpass.getuser()
            home_dir = str(Path.home())
            desktop_dir = str(Path.home() / "Desktop")
            documents_dir = str(Path.home() / "Documents")
            downloads_dir = str(Path.home() / "Downloads")

            # 获取计算机名
            computer_name = os.environ.get('COMPUTERNAME', '')

            # 获取系统盘符列表
            available_drives = []
            for drive in range(ord('A'), ord('Z') + 1):
                drive_letter = chr(drive) + ":\\"
                if os.path.exists(drive_letter):
                    available_drives.append(drive_letter)

            logger.info(f"成功获取系统信息: 用户={username}")

            return {
                "status": "success",
                "message": "成功获取系统信息",
                "username": username,
                "computer_name": computer_name,
                "paths": {
                    "home": home_dir,
                    "desktop": desktop_dir,
                    "documents": documents_dir,
                    "downloads": downloads_dir
                },
                "drives": available_drives
            }
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {
                "status": "error",
                "message": f"获取系统信息失败: {str(e)}"
            }

# 注册工具
ToolRegistry.register(SystemInfoTool())