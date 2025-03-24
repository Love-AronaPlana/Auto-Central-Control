"""工具模块

该模块提供了ACC系统使用的各种工具。
"""

# 导入基础工具类和注册表
from ACC.tool.base import BaseTool, ToolRegistry, execute_tool

# 导入所有工具类
from .execute_command import ExecuteCommandTool
from .write_files import WriteFileTool
from .file_operations.create_file import CreateFileTool
from .file_operations.create_multiple_files import CreateMultipleFilesTool
from .read_file import ReadFileTool
from .list_directory import ListDirectoryTool
from .file_operations.delete_file import DeleteFileTool
from .file_operations.delete_multiple_files import DeleteMultipleFilesTool
from .system_info import SystemInfoTool
from .python_interpreter import PythonInterpreterTool
from .image_recognition import ImageRecognitionTool
from .web_search.search_bing import SearchBingTool
from .web_search.search_baidu import SearchBaiduTool
from .web_search.search_google import SearchGoogleTool

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
    "ImageRecognitionTool",
    "SearchBingTool",
    "SearchBaiduTool",
    "SearchGoogleTool",
]

from .file_operations.create_file import CreateFileTool
from .file_operations.create_multiple_files import CreateMultipleFilesTool

# 注册所有工具
ToolRegistry.register(WriteFileTool())
ToolRegistry.register(ExecuteCommandTool())
ToolRegistry.register(CreateFileTool())
ToolRegistry.register(CreateMultipleFilesTool())
ToolRegistry.register(ReadFileTool())
ToolRegistry.register(ListDirectoryTool())
ToolRegistry.register(DeleteFileTool())
ToolRegistry.register(DeleteMultipleFilesTool())
ToolRegistry.register(SystemInfoTool())
ToolRegistry.register(PythonInterpreterTool())
ToolRegistry.register(ImageRecognitionTool())
ToolRegistry.register(SearchBingTool())
ToolRegistry.register(SearchBaiduTool())
ToolRegistry.register(SearchGoogleTool())

__all__ = ["BaseTool", "ToolRegistry", "execute_tool", "register_all_tools"]
