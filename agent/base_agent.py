#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
agent/base_agent.py - 基础Agent类

该模块提供了所有特定Agent的基类，包含与OpenAI API通信的通用功能。
"""

import os
import json
import requests
import logging
import time  # 新增导入
from typing import List, Dict, Any, Optional


class BaseAgent:
    """
    基础Agent类，提供与OpenAI API通信的通用功能
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化基础Agent

        Args:
            config: 系统配置信息，包含API URL、API Key等
        """
        self.api_url = config["api_url"]
        self.api_key = config["api_key"]
        self.model_name = config["model_name"]
        self.max_tokens = config["max_tokens"]
        self.debug = config.get("debug", False)
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_system_prompt(self) -> str:
        """
        获取系统提示词的抽象方法，子类必须实现该方法

        该方法定义了一个标准接口用于获取不同Agent的提示词模板。
        子类需要根据具体任务类型返回对应的系统级提示词。

        返回:
            str: 符合OpenAI API格式的系统角色提示词字符串，
                 通常包含任务说明、响应格式要求等内容

        异常:
            NotImplementedError: 如果子类未实现该方法时抛出

        示例:
            >>> class MyAgent(BaseAgent):
            ...     def get_system_prompt(self):
            ...         return "你是一个助手..."
        """
        raise NotImplementedError("子类必须实现get_system_prompt方法")

    def call_api(
        self, messages: List[Dict[str, str]], temperature: float = 0.7
    ) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            # 仅当 max_tokens 有效时添加该参数
            **({"max_tokens": self.max_tokens} if self.max_tokens > 0 else {}),
        }

        if self.debug:
            self.logger.debug(
                f"[API请求] 开始请求 | 模型: {self.model_name} | 温度: {temperature}"
            )
            self.logger.debug(f"[API请求] 完整请求头: {headers}")
            self.logger.debug(
                f"[API请求] 请求正文:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
            )

        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30,  # 添加超时参数
            )
            elapsed_time = time.time() - start_time

            if self.debug:
                self.logger.debug(f"[API响应] 请求耗时: {elapsed_time:.2f}秒")
                self.logger.debug(f"[API响应] 状态码: {response.status_code}")
                self.logger.debug(f"[API响应] 原始响应头:\n{dict(response.headers)}")
                self.logger.debug(
                    f"[API响应] 响应正文:\n{response.text[:1000]}"
                )  # 截取前1000字符防止日志过长

            response.raise_for_status()
            result = response.json()

            return result
        except Exception as e:
            # 处理请求未发出时的耗时计算
            elapsed_time = time.time() - start_time if "start_time" in locals() else 0.0
            self.logger.error(
                f"[API错误] 请求失败 | 耗时: {elapsed_time:.2f}秒 | 错误: {str(e)}"
            )
            if hasattr(response, "text"):
                self.logger.error(f"[API错误] 错误响应正文: {response.text[:500]}")
            raise

    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理API响应，提取JSON内容

        Args:
            response: API响应

        Returns:
            Dict[str, Any]: 解析后的JSON内容
        """
        try:
            content = response["choices"][0]["message"]["content"]

            # 新增预处理：去除Markdown代码块标记并美化JSON
            if content.startswith("```json"):
                content = content[7:]  # 去除开头的```json
            if content.endswith("```"):
                content = content[:-3]

            # 解析后重新格式化为美化后的JSON
            parsed_json = json.loads(content)
            return json.loads(json.dumps(parsed_json, indent=2, ensure_ascii=False))

        except Exception as e:
            self.logger.error(f"解析响应失败: {str(e)}")
            self.logger.error(f"原始响应内容: {content}")
            raise ValueError(f"无法解析响应为JSON: {str(e)}")

    def process(self, *args, **kwargs) -> Dict[str, Any]:
        """
        处理请求，子类需要重写此方法

        Returns:
            Dict[str, Any]: 处理结果
        """
        raise NotImplementedError("子类必须实现process方法")
