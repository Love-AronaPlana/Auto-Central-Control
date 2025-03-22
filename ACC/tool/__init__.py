"""工具模块

该模块提供了ACC系统使用的各种工具。
"""

# 导入基础工具类和注册表
from ACC.tool.base import BaseTool, ToolRegistry, execute_tool

# 导入所有工具类
from .execute_command import ExecuteCommandTool
from .write_files import WriteFileTool
from .create_files import CreateFileTool, CreateMultipleFilesTool
from .read_file import ReadFileTool
from .list_directory import ListDirectoryTool
from .delete_files import DeleteFileTool, DeleteMultipleFilesTool
from .system_info import SystemInfoTool
from .python_interpreter import PythonInterpreterTool

# 导出所有工具类
__all__ = [
    "ExecuteCommandTool",
    "WriteFileTool",
    "CreateFileTool",
    "CreateMultipleFilesTool",
    "ReadFileTool",
    "ListDirectoryTool",
    "DeleteFileTool",
    "DeleteMultipleFilesTool",
    "SystemInfoTool",
    "PythonInterpreterTool",
]

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
