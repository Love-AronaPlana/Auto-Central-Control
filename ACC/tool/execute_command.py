"""执行命令工具

该模块提供了执行命令的工具，允许AI执行bash/cmd命令。
所有命令执行操作都应通过该工具进行，以确保安全性和一致性。
"""

import os
import subprocess
import platform
import logging
import shlex
import locale
from typing import Dict, Any, Optional

from ACC.tool.base import BaseTool

logger = logging.getLogger(__name__)


class ExecuteCommandTool(BaseTool):
    """执行命令工具"""

    def __init__(self):
        """初始化执行命令工具"""
        super().__init__(
            name="execute_command",
            description="在指定绝对路径目录执行命令并返回结果",  # 修改描述
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行命令

        Args:
            **kwargs: 工具参数，包括：
                command: 要执行的命令
                working_dir: 执行目录的绝对路径（新增参数）
                timeout: 命令执行超时时间（秒），默认30秒

        Returns:
            执行结果字典
        """
        # 从kwargs中提取参数
        command = kwargs.get("command")
        working_dir = kwargs.get("working_dir", os.getcwd())  # 新增参数
        timeout = kwargs.get("timeout", 30)

        # 验证必要参数
        if not command:
            return {
                "status": "error",
                "message": "缺少必要参数: command",
                "exit_code": -1,
                "stdout": "",
                "stderr": "Missing required parameter: command",
                "command": command,
                "working_dir": working_dir,  # 返回绝对路径
            }

        try:
            # 处理工作目录为绝对路径
            abs_working_dir = os.path.abspath(working_dir)

            # 确保目录存在
            os.makedirs(abs_working_dir, exist_ok=True)

            # 根据操作系统选择不同的命令执行方式
            current_os = platform.system()

            # 记录执行的命令和目录
            logger.info(f"在目录 {abs_working_dir} 执行命令: {command}")

            # 获取系统默认编码
            system_encoding = locale.getpreferredencoding()
            logger.debug(f"系统默认编码: {system_encoding}")

            # 执行命令（修改cwd参数为abs_working_dir）
            if current_os == "Windows":
                # 在Windows上，使用系统默认编码
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=abs_working_dir,  # 使用绝对路径
                    text=True,
                    encoding=system_encoding,  # 使用系统默认编码
                    errors="replace",
                )
            else:
                args = shlex.split(command)
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=abs_working_dir,  # 使用绝对路径
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )

            # 等待命令执行完成，设置超时时间
            stdout, stderr = process.communicate(timeout=timeout)
            exit_code = process.returncode

            # 构建返回结果
            result = {
                "status": "success" if exit_code == 0 else "error",
                "message": "命令执行成功" if exit_code == 0 else "命令执行失败",
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "command": command,
            }

            # 在返回结果中添加工作目录信息
            result["working_dir"] = abs_working_dir
            return result

        except subprocess.TimeoutExpired:
            # 在超时错误返回中添加目录信息
            return {
                "status": "error",
                "message": f"命令执行超时（超过{timeout}秒）",
                "exit_code": -1,
                "stdout": "",
                "stderr": "Command timed out",
                "command": command,
                "working_dir": abs_working_dir,  # 返回绝对路径
            }
        except Exception as e:
            # 在异常返回中添加目录信息
            return {
                "status": "error",
                "message": f"命令执行失败: {str(e)}",
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "command": command,
                "working_dir": abs_working_dir,  # 返回绝对路径
            }
