#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工作流主模块
负责控制整个系统的工作流程
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 导入模块
from modules.openai_api import OpenAIAPI
from modules.prompt_manager import PromptManager
from modules.tool_manager import ToolManager
from modules.memory_manager import MemoryManager

# 获取日志记录器
logger = logging.getLogger("ACC")


def start_workflow(debug: bool = False) -> None:
    """
    启动工作流

    Args:
        debug: 是否开启调试模式
    """
    logger.info("初始化工作流...")

    # 初始化各个模块
    openai_api = OpenAIAPI(debug=debug)
    prompt_manager = PromptManager()

    # 移除原有提示词加载逻辑，始终获取用户输入
    user_input = input("\n请输入您的要求：")
    prompt_manager.user_prompts = [user_input]

    tool_manager = ToolManager()
    # 在初始化记忆管理器部分
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    memory_manager = MemoryManager(session_id=session_id)
    conversation_history = memory_manager.load_conversation()

    # 加载系统提示词
    system_prompt = prompt_manager.get_system_prompt()

    # 加载指定角色的模块提示词
    modules_prompt = prompt_manager.get_modules_prompt()

    # 加载助手提示词
    assistant_prompt = prompt_manager.get_assistant_prompt()

    # 初始化对话历史
    system_prompt = prompt_manager.get_system_prompt()
    conversation_history = memory_manager.init_conversation(
        system_prompt
    )  # 添加system_prompt参数

    # 工作流循环
    try:
        while True:
            # 获取当前提示词
            current_prompt = prompt_manager.get_current_prompt()

            # 准备发送给AI的消息
            messages = [
                {"role": "system", "content": system_prompt},
                *conversation_history,
            ]

            messages.append({"role": "system", "content": modules_prompt})

            messages.append({"role": "assistant", "content": assistant_prompt})

            if current_prompt:
                messages.append({"role": "user", "content": current_prompt})

            # 获取可用工具
            available_tools = tool_manager.get_available_tools()

            # 调用OpenAI API
            response = openai_api.send_request(messages=messages, tools=available_tools)

            # 处理响应
            if response:
                # 解析响应
                parsed_response = openai_api.parse_response(response)

                # 处理工具调用
                # if "tool_calls" in parsed_response:
                #     for tool_call in parsed_response["tool_calls"]:
                #         # 执行工具调用
                #         tool_result = tool_manager.execute_tool(
                #             tool_call["name"], tool_call["arguments"]
                #         )

                #         # 将工具调用结果添加到对话历史
                #         conversation_history.append(
                #             {
                #                 "role": "assistant",
                #                 "content": None,
                #                 "tool_calls": [
                #                     {
                #                         "id": tool_call["id"],
                #                         "type": "function",
                #                         "function": {
                #                             "name": tool_call["name"],
                #                             "arguments": json.dumps(
                #                                 tool_call["arguments"]
                #                             ),
                #                         },
                #                     }
                #                 ],
                #             }
                #         )

                #         conversation_history.append(
                #             {
                #                 "role": "tool",
                #                 "tool_call_id": tool_call["id"],
                #                 "content": json.dumps(tool_result),
                #             }
                #         )
                # else:
                #     # 将AI响应添加到对话历史
                #     conversation_history.append(
                #         {"role": "assistant", "content": parsed_response["content"]}
                #     )

                # 将AI响应添加到对话历史
                conversation_history.append(
                    {"role": "assistant", "content": parsed_response["content"]}
                )

                # 保存对话历史
                memory_manager.save_conversation(conversation_history)

            # 检查是否需要继续循环
            # if prompt_manager.should_continue() is False:
            #     break

    except KeyboardInterrupt:
        logger.info("用户中断工作流")
    except Exception as e:
        logger.error(f"工作流执行出错: {e}", exc_info=True)

    logger.info("工作流结束")
