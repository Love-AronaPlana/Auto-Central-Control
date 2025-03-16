# 代理工作流模块

import json
import asyncio
from typing import Dict, List, Any, Optional
from config.logging_config import get_logger
from config.constants import (
    STATUS_IDLE,
    STATUS_ANALYZING,
    STATUS_SELECTING_TOOL,
    STATUS_EXECUTING,
    STATUS_PROCESSING_RESULT,
    STATUS_COMPLETED,
)
from modules.api_client import ApiClient
from prompts.system_prompt import get_system_prompt
from prompts.analyzer_prompt import get_analyzer_prompt
from prompts.tool_selector_prompt import get_tool_selector_prompt
from prompts.result_processor_prompt import get_result_processor_prompt
from tools.file_tools import file_read, file_write

# 获取日志记录器
logger = get_logger(__name__)


class AgentWorkflow:
    """代理工作流

    负责协调各个组件的工作，确保系统按照预定的流程执行任务。
    实现了事件分析、工具选择、执行和结果处理的完整流程。
    """

    def __init__(self):
        """初始化代理工作流"""
        self.api_client = ApiClient()
        self.status = STATUS_IDLE
        self.messages = []
        self.tools = {"file_read": file_read, "file_write": file_write}

    def add_user_message(self, content: str) -> None:
        """添加用户消息

        Args:
            content (str): 消息内容
        """
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        """添加助手消息

        Args:
            content (str): 消息内容
        """
        self.messages.append({"role": "assistant", "content": content})

    def add_function_message(self, name: str, content: Dict[str, Any]) -> None:
        """添加函数消息

        Args:
            name (str): 函数名称
            content (Dict[str, Any]): 函数返回内容
        """
        self.messages.append(
            {
                "role": "function",
                "name": name,
                "content": json.dumps(content, ensure_ascii=False),
            }
        )

    async def analyze_event(self) -> Dict[str, Any]:
        response = await self.api_client.send_request_stream(
            get_analyzer_prompt(), self.messages
        )

        # 新增原始响应日志
        logger.debug(
            "原始分析结果：\n%s", json.dumps(response, indent=2, ensure_ascii=False)
        )

        # 解析响应
        if "error" in response:
            logger.error(f"事件分析失败: {response['error']}")
            return {"error": response["error"]}

        content = response["choices"][0]["message"]["content"]
        try:
            analysis_result = json.loads(content)
            logger.info("事件分析完成")
            return analysis_result
        except json.JSONDecodeError:
            logger.error("解析事件分析结果失败，返回内容不是有效的JSON")
            return {"error": "解析事件分析结果失败，返回内容不是有效的JSON"}

    async def select_tool(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """选择工具

        根据分析结果选择合适的工具，作为执行任务的基础。

        Args:
            analysis_result (Dict[str, Any]): 分析结果

        Returns:
            Dict[str, Any]: 工具选择结果
        """
        self.status = STATUS_SELECTING_TOOL
        logger.info("开始选择工具")

        # 添加分析结果到消息历史
        self.add_assistant_message(json.dumps(analysis_result, ensure_ascii=False))

        # 发送请求给工具选择器
        response = await self.api_client.send_request_stream(
            get_tool_selector_prompt(), self.messages
        )

        # 解析响应
        if "error" in response:
            logger.error(f"工具选择失败: {response['error']}")
            return {"error": response["error"]}

        content = response["choices"][0]["message"]["content"]
        try:
            tool_selection = json.loads(content)
            logger.info(f"选择了工具: {tool_selection['selected_tool']}")
            return tool_selection
        except json.JSONDecodeError:
            logger.error("解析工具选择结果失败，返回内容不是有效的JSON")
            return {"error": "解析工具选择结果失败，返回内容不是有效的JSON"}

    async def execute_tool(self, tool_selection: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具

        执行选择的工具，获取执行结果。

        Args:
            tool_selection (Dict[str, Any]): 工具选择结果

        Returns:
            Dict[str, Any]: 执行结果
        """
        self.status = STATUS_EXECUTING
        tool_name = tool_selection.get("selected_tool")
        parameters = tool_selection.get("parameters", {})

        logger.info(f"开始执行工具: {tool_name}")

        # 添加工具选择结果到消息历史
        self.add_assistant_message(json.dumps(tool_selection, ensure_ascii=False))

        # 检查工具是否存在
        if tool_name not in self.tools:
            error_msg = f"工具不存在: {tool_name}"
            logger.error(error_msg)
            return {"error": error_msg}

        # 执行工具
        try:
            result = self.tools[tool_name](**parameters)
            logger.info(f"工具执行完成: {tool_name}")

            # 添加执行结果到消息历史
            self.add_function_message(tool_name, result)

            return result
        except Exception as e:
            error_msg = f"执行工具时出错: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def process_result(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """处理结果

        分析工具执行的结果，作为后续决策的基础。

        Args:
            execution_result (Dict[str, Any]): 执行结果

        Returns:
            Dict[str, Any]: 处理结果
        """
        self.status = STATUS_PROCESSING_RESULT
        logger.info("开始处理执行结果")

        # 发送请求给结果处理器
        response = await self.api_client.send_request_stream(
            get_result_processor_prompt(), self.messages
        )

        # 解析响应
        if "error" in response:
            logger.error(f"结果处理失败: {response['error']}")
            return {"error": response["error"]}

        content = response["choices"][0]["message"]["content"]
        try:
            processing_result = json.loads(content)
            logger.info("结果处理完成")

            # 添加处理结果到消息历史
            self.add_assistant_message(
                json.dumps(processing_result, ensure_ascii=False)
            )

            return processing_result
        except json.JSONDecodeError:
            logger.error("解析结果处理结果失败，返回内容不是有效的JSON")
            return {"error": "解析结果处理结果失败，返回内容不是有效的JSON"}

    async def generate_response(self) -> str:
        """生成最终响应

        根据整个处理流程生成最终响应给用户。

        Returns:
            str: 最终响应
        """
        self.status = STATUS_COMPLETED
        logger.info("开始生成最终响应")

        # 发送请求给系统
        response = await self.api_client.send_request_stream(
            get_system_prompt(), self.messages
        )

        # 解析响应
        if "error" in response:
            logger.error(f"生成最终响应失败: {response['error']}")
            return json.dumps({"error": response["error"]}, ensure_ascii=False)

        content = response["choices"][0]["message"]["content"]

        # 添加最终响应到消息历史
        self.add_assistant_message(content)

        logger.info("最终响应生成完成")
        return content

    async def run(self, user_input: str) -> str:
        """运行代理工作流

        执行完整的代理工作流程，包括事件分析、工具选择、执行和结果处理。

        Args:
            user_input (str): 用户输入

        Returns:
            str: 最终响应
        """
        # 添加用户输入到消息历史
        self.add_user_message(user_input)

        # 分析事件
        analysis_result = await self.analyze_event()
        if "error" in analysis_result:
            return json.dumps({"error": analysis_result["error"]}, ensure_ascii=False)

        # 选择工具
        tool_selection = await self.select_tool(analysis_result)
        if "error" in tool_selection:
            return json.dumps({"error": tool_selection["error"]}, ensure_ascii=False)

        # 执行工具
        execution_result = await self.execute_tool(tool_selection)
        if "error" in execution_result:
            return json.dumps({"error": execution_result["error"]}, ensure_ascii=False)

        # 处理结果
        processing_result = await self.process_result(execution_result)
        if "error" in processing_result:
            return json.dumps({"error": processing_result["error"]}, ensure_ascii=False)

        # 检查是否需要继续执行
        if (
            processing_result.get("next_actions")
            and len(processing_result["next_actions"]) > 0
        ):
            # 递归执行下一步
            return await self.run("继续执行下一步操作")

        # 生成最终响应
        return await self.generate_response()
