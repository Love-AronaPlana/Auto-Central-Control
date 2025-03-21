"""工具模块基础类

该模块提供了工具调用的基础类，所有工具都应继承自该类。
工具类负责定义工具的名称、描述、参数和执行逻辑。
"""

import json
import logging
import os
import time  # 新增导入
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """工具基础类"""

    def __init__(self, name: str, description: str):
        """初始化工具

        Args:
            name: 工具名称
            description: 工具描述
        """
        self.name = name
        self.description = description

    def log_debug(self, message: str):
        """记录DEBUG级别日志

        Args:
            message: 日志消息
        """
        logger.debug(f"[工具:{self.name}] {message}")

    def log_info(self, message: str):
        """记录INFO级别日志

        Args:
            message: 日志消息
        """
        logger.info(f"[工具:{self.name}] {message}")

    def log_error(self, message: str):
        """记录ERROR级别日志

        Args:
            message: 日志消息
        """
        logger.error(f"[工具:{self.name}] {message}")

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            执行结果字典
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            工具字典
        """
        return {"name": self.name, "description": self.description}


class ToolRegistry:
    """工具注册表，用于管理所有可用的工具"""

    _tools: Dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool: BaseTool):
        """注册工具

        Args:
            tool: 工具实例
        """
        cls._tools[tool.name] = tool
        logger.info(f"注册工具: {tool.name}")
        # 添加debug级别的详细日志
        logger.debug(f"已注册工具 '{tool.name}' - 描述: {tool.description}")

    @classmethod
    def get_tool(cls, name: str) -> Optional[BaseTool]:
        """获取工具

        Args:
            name: 工具名称

        Returns:
            工具实例，如果不存在则返回None
        """
        return cls._tools.get(name)

    @classmethod
    def get_all_tools(cls) -> List[BaseTool]:
        """获取所有工具

        Returns:
            工具实例列表
        """
        return list(cls._tools.values())

    @classmethod
    def get_tools_dict(cls) -> List[Dict[str, Any]]:
        """获取工具字典列表

        Returns:
            工具字典列表
        """
        tools_dict = []
        for name, tool in cls._tools.items():
            tool_dict = {
                "type": "function",  # 添加必要的type字段
                "function": {"none": "none"},
            }
            tools_dict.append(tool_dict)
        return tools_dict


def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """执行工具

    Args:
        tool_name: 工具名称
        **kwargs: 工具参数

    Returns:
        执行结果字典
    """
    logger.debug(
        f"准备执行工具: {tool_name}，参数详情: {json.dumps(kwargs, ensure_ascii=False)}"
    )

    tool = ToolRegistry.get_tool(tool_name)
    if not tool:
        logger.error(f"工具不存在: {tool_name}")
        return {"error": f"工具不存在: {tool_name}"}

    try:
        logger.info(f"开始执行工具: {tool_name}，参数类型: {', '.join(kwargs.keys())}")
        tool.log_debug(f"执行开始，参数: {json.dumps(kwargs, ensure_ascii=False)}")

        start_time = time.time()
        result = tool.execute(**kwargs)
        execution_time = time.time() - start_time

        tool.log_info(f"执行完成，耗时: {execution_time:.2f}秒")
        tool.log_debug(f"执行结果: {json.dumps(result, ensure_ascii=False)}")

        logger.info(
            f"工具执行成功: {tool_name}，状态: {result.get('status', 'unknown')}"
        )
        return result
    except Exception as e:
        tool.log_error(f"执行异常: {str(e)}")
        logger.error(f"工具执行失败: {tool_name}，错误: {e}")
        import traceback

        logger.debug(f"工具执行异常堆栈: {traceback.format_exc()}")
        return {"error": f"工具执行失败: {e}"}
