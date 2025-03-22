"""工具模块

该模块提供了ACC系统使用的各种工具。
"""

# 导入基础工具类和注册表
from ACC.tool.base import BaseTool, ToolRegistry, execute_tool

# 导入所有工具
from ACC.tool.execute_command import ExecuteCommandTool
from ACC.tool.write_files import WriteFileTool  # 导入新的写入文件工具
from ACC.tool.create_files import (
    CreateFileTool,
    CreateMultipleFilesTool,
)
from ACC.tool.open_files import ReadFileTool, ListDirectoryTool
from ACC.tool.delete_files import DeleteFileTool, DeleteMultipleFilesTool
from ACC.tool.system_info import SystemInfoTool
from ACC.tool.python_interpreter import PythonInterpreterTool  # 导入新的Python解释器工具

# 注册所有工具
ToolRegistry.register(ExecuteCommandTool())
ToolRegistry.register(WriteFileTool())
ToolRegistry.register(CreateFileTool())
ToolRegistry.register(CreateMultipleFilesTool())
ToolRegistry.register(ReadFileTool())
ToolRegistry.register(ListDirectoryTool())
ToolRegistry.register(DeleteFileTool())
ToolRegistry.register(DeleteMultipleFilesTool())
ToolRegistry.register(SystemInfoTool())
ToolRegistry.register(PythonInterpreterTool())  # 注册Python解释器工具

__all__ = ["BaseTool", "ToolRegistry", "execute_tool", "register_all_tools"]
