#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OpenAI API模块
负责与OpenAI API通信，发送请求并处理响应
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union

# 获取日志记录器
logger = logging.getLogger("ACC")


class OpenAIAPI:
    """
    OpenAI API接口类
    负责与OpenAI API通信，发送请求并处理响应
    """

    def __init__(self, debug: bool = False):
        """
        初始化OpenAI API接口

        Args:
            debug: 是否开启调试模式
        """
        self.debug = debug
        self.api_url = os.getenv("API_URL", "https://api.openai.com/v1")
        self.api_key = os.getenv("API_KEY", "")
        self.model = os.getenv("MODEL", "gpt-4-turbo")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "8192"))

        if not self.api_key:
            logger.error("API_KEY未设置，请在.env文件中配置")
            raise ValueError("API_KEY未设置，请在.env文件中配置")

        logger.info(f"初始化OpenAI API接口，模型：{self.model}")

    def send_request(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        发送请求到OpenAI API

        Args:
            messages: 消息列表
            tools: 工具列表

        Returns:
            API响应结果
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
        }

        if tools:
            payload["tools"] = tools

        # 调试模式下打印请求信息
        if self.debug:
            debug_payload = payload.copy()
            # 不打印完整的消息内容，避免日志过大
            # debug_payload["messages"] = f"[{len(messages)}条消息]"
            logger.debug(
                f"发送请求到OpenAI API: {json.dumps(debug_payload, ensure_ascii=False)}"
            )

        try:
            response = requests.post(
                f"{self.api_url}/chat/completions", headers=headers, json=payload
            )

            response.raise_for_status()
            result = response.json()

            if self.debug:
                logger.debug(
                    f"收到OpenAI API响应: {json.dumps(result, ensure_ascii=False)}"
                )

            return result

        except Exception as e:
            logger.error(f"请求OpenAI API出错: {e}")
            return None

    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析OpenAI API响应

        Args:
            response: API响应结果

        Returns:
            解析后的响应结果
        """
        try:
            # 获取响应中的第一个选择
            choice = response.get("choices", [])[0]
            message = choice.get("message", {})

            # 解析响应内容
            result = {}

            # 检查是否有工具调用
            if "tool_calls" in message:
                tool_calls = []

                for tool_call in message.get("tool_calls", []):
                    # 解析工具调用参数
                    function = tool_call.get("function", {})
                    arguments = function.get("arguments", "{}")

                    try:
                        # 将JSON字符串解析为Python对象
                        args = json.loads(arguments)
                    except json.JSONDecodeError:
                        logger.warning(f"解析工具调用参数出错: {arguments}")
                        args = {}

                    # 添加到工具调用列表
                    tool_calls.append(
                        {
                            "id": tool_call.get("id", ""),
                            "name": function.get("name", ""),
                            "arguments": args,
                        }
                    )

                result["tool_calls"] = tool_calls

            # 检查是否有内容
            if "content" in message and message["content"]:
                result["content"] = message["content"]

            return result

        except Exception as e:
            logger.error(f"解析OpenAI API响应出错: {e}")
            return {"content": "解析响应出错"}
