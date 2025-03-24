"""系统信息工具

该模块提供了获取系统信息的工具，包括用户信息和系统路径等。
"""

import os
import logging
import getpass
import subprocess  # 添加缺少的导入
from pathlib import Path
from typing import Dict, Any, Optional, List

from ACC.tool.base import BaseTool, ToolRegistry

import platform
import socket

logger = logging.getLogger(__name__)

class SystemInfoTool(BaseTool):
    """系统信息工具（支持Windows/Linux）"""

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
            
            # 跨平台路径获取
            if platform.system() == 'Windows':
                desktop_dir = str(Path.home() / "Desktop")
                documents_dir = str(Path.home() / "Documents")
                downloads_dir = str(Path.home() / "Downloads")
                computer_name = os.environ.get('COMPUTERNAME', '')
            else:  # Linux/MacOS
                desktop_dir = self._get_linux_special_dir("DESKTOP") or str(Path.home() / "Desktop")
                documents_dir = self._get_linux_special_dir("DOCUMENTS") or str(Path.home() / "Documents")
                downloads_dir = self._get_linux_special_dir("DOWNLOAD") or str(Path.home() / "Downloads")
                computer_name = socket.gethostname()

            # 跨平台驱动器/挂载点检测
            available_drives = self._get_system_drives()
            
            logger.info(f"成功获取系统信息[{platform.system()}]: 用户={username}")

            return {
                "status": "success",
                "message": "成功获取系统信息",
                "username": username,
                "computer_name": computer_name,
                "paths": {
                    "home": home_dir.replace('\\', '/'),
                    "desktop": desktop_dir.replace('\\', '/'),
                    "documents": documents_dir.replace('\\', '/'),
                    "downloads": downloads_dir.replace('\\', '/')
                },
                "drives": available_drives,
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version()
                }
            }
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {"status": "error", "message": str(e)}

    def _get_linux_special_dir(self, dir_type: str) -> Optional[str]:
        """获取Linux特殊目录（使用xdg-user-dir命令）"""
        try:
            result = subprocess.run(
                ['xdg-user-dir', dir_type],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
        return None

    def _get_system_drives(self) -> List[str]:
        """获取系统驱动器/挂载点"""
        if platform.system() == 'Windows':
            return [f"{d}:\\" for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f"{d}:\\")]
        else:
            # 获取Linux挂载点（排除虚拟文件系统）
            return [os.path.join(os.sep, d) for d in os.listdir(os.sep) 
                   if os.path.ismount(os.path.join(os.sep, d)) and not d.startswith(('proc', 'sys', 'dev'))]

# 注册工具
ToolRegistry.register(SystemInfoTool())