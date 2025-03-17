#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具管理模块
负责管理和执行AI可用的工具
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

# 获取日志记录器
logger = logging.getLogger("ACC")


class ToolManager:
    """
    工具管理类
    负责管理和执行AI可用的工具
    """

    def __init__(self):
        """
        初始化工具管理器
        """
        self.tools_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"
        )
        self.workspace_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace"
        )

        # 确保工具目录和工作空间目录存在
        if not os.path.exists(self.tools_dir):
            os.makedirs(self.tools_dir)
        if not os.path.exists(self.workspace_dir):
            os.makedirs(self.workspace_dir)

        # 从JSON文件加载工具列表
        tools_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "prompts",
            "tools.json",
        )
        try:
            with open(tools_path, "r", encoding="utf-8") as f:
                self.tools = json.load(f)
            logger.info(f"成功从 {tools_path} 加载 {len(self.tools)} 个工具")
        except Exception as e:
            logger.error(f"加载工具配置文件失败: {e}")
            raise RuntimeError(
                f"无法加载工具配置文件 {tools_path}，请确保文件存在且格式正确"
            )

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        获取可用工具列表

        Returns:
            可用工具列表
        """
        return self.tools

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        logger.info(
            f"执行工具: {tool_name}, 参数: {json.dumps(arguments, ensure_ascii=False)}"
        )

        try:
            if tool_name == "file_read":
                return self._file_read(arguments)
            elif tool_name == "file_write":
                return self._file_write(arguments)
            else:
                logger.warning(f"未知工具: {tool_name}")
                return {"error": f"未知工具: {tool_name}"}
        except Exception as e:
            logger.error(f"执行工具出错: {e}", exc_info=True)
            return {"error": f"执行工具出错: {str(e)}"}

    def _file_read(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        读取文件内容

        Args:
            arguments: 工具参数

        Returns:
            文件内容
        """
        file_path = arguments.get("file_path", "")

        # 确保文件路径在工作空间内
        if not file_path.startswith(self.workspace_dir):
            file_path = os.path.join(self.workspace_dir, file_path)

        if not os.path.exists(file_path):
            return {"error": f"文件不存在: {file_path}"}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"content": content}
        except Exception as e:
            return {"error": f"读取文件出错: {str(e)}"}

    def _file_write(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        写入文件内容

        Args:
            arguments: 工具参数

        Returns:
            写入结果
        """
        file_path = arguments.get("file_path", "")
        content = arguments.get("content", "")
        mode = arguments.get("mode", "w")

        # 确保文件路径在工作空间内
        if not file_path.startswith(self.workspace_dir):
            file_path = os.path.join(self.workspace_dir, file_path)

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            with open(file_path, mode, encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "message": f"文件写入成功: {file_path}"}
        except Exception as e:
            return {"error": f"写入文件出错: {str(e)}"}
