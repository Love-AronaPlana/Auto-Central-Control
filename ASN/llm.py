"""LLM模块，负责与OpenAI API通信

该模块提供了与OpenAI API通信的接口，所有需要与AI模型交互的模块都应通过该模块进行。
模块会读取配置文件中的API设置，并提供发送请求和接收响应的功能。
"""

import json
import logging
import os
from typing import Dict, List, Optional, Union, Any

import requests

from ASN.config import get_config, get_llm_config

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM客户端，负责与OpenAI API通信"""

    def __init__(self):
        """初始化LLM客户端"""
        self.config = get_llm_config()
        self.debug = self.config.get("debug", False)

        # 新增调试日志验证配置加载
        logger.debug("🔍 [调试模式] LLM配置已加载")
        logger.debug(f"当前调试模式状态: {self.debug}")
        logger.debug(
            f"完整配置内容: {json.dumps(self.config, indent=2, ensure_ascii=False)}"
        )

        # 添加缺失的属性初始化
        self.base_url = self.config.get("base_url", "https://api.openai.com/v1")
        self.api_key = self.config.get("api_key", "")
        self.model = self.config.get("model", "gpt-4")  # 添加model属性
        self.max_tokens = self.config.get("max_tokens", 4096)
        self.temperature = self.config.get("temperature", 0.0)
        self.api_type = self.config.get("api_type", "openai")
        self.api_version = self.config.get("api_version", None)

        self._validate_config()  # 确保配置验证
        logger.info(f"LLM客户端初始化完成，使用模型: {self.model}")

    def _validate_config(self):
        """验证配置信息"""
        if not self.api_key:
            logger.error("API密钥未配置")
            raise ValueError("API密钥未配置，请在config.toml中设置api_key")

        if not self.base_url:
            logger.error("API URL未配置")
            raise ValueError("API URL未配置，请在config.toml中设置base_url")

    def _prepare_headers(self) -> Dict[str, str]:
        """准备请求头

        Returns:
            请求头字典
        """
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_type == "azure":
            headers["api-key"] = self.api_key
            if self.api_version:
                headers["api-version"] = self.api_version
        else:  # openai
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def send_request(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> Union[Dict[str, Any], Any]:
        """发送请求到OpenAI API

        Args:
            messages: 消息列表，包含角色和内容
            model: 模型名称，默认使用配置中的模型
            temperature: 温度参数，控制随机性，默认使用配置中的温度
            max_tokens: 最大生成token数，默认使用配置中的最大token数
            stream: 是否使用流式响应，默认为False
            tools: 工具列表，默认为None
            tool_choice: 工具选择，默认为None

        Returns:
            API响应字典或流式响应生成器
        """
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens

        # 构建请求URL
        url = f"{self.base_url}/chat/completions"
        headers = self._prepare_headers()
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        # 添加工具信息
        if tools:
            data["tools"] = tools

        if tool_choice:
            data["tool_choice"] = tool_choice

        # 发送请求
        # 在发送请求前添加调试日志
        if self.debug:
            logger.debug("⬆️ 即将发送API请求:")
            logger.debug(f"URL: {url}")
            logger.debug(f"Headers: {headers}")
            logger.debug(
                f"Request Body: {json.dumps(data, indent=2, ensure_ascii=False)}"
            )

        try:
            headers = self._prepare_headers()

            # 处理流式响应
            if stream:
                return self._handle_streaming_response(url, headers, data)

            # 处理普通响应
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            # 调试模式下记录完整响应
            if self.debug:
                logger.debug("⬇️ 收到API响应:")
                # logger.debug(f"Status Code: {response.status_code}")
                # logger.debug(f"Response Body: {response.text}")

                # logger.debug("✅ [调试模式] API响应详情")
                logger.debug(f"Status Code: {response.status_code}")
                logger.debug(f"Response Headers: {dict(response.headers)}")
                logger.debug(f"Full Response: {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            if hasattr(e, "response") and e.response:
                logger.error(f"响应状态码: {e.response.status_code}")
                logger.error(f"响应内容: {e.response.text}")
            raise

    def _handle_streaming_response(
        self, url: str, headers: Dict[str, str], data: Dict[str, Any]
    ):
        # 在流式处理中添加调试日志
        if self.debug:
            logger.debug("🔍 [调试模式] 开始处理流式响应")  # ✅ 流式处理日志

        try:
            with requests.post(
                url, headers=headers, json=data, stream=True
            ) as response:
                if self.debug:
                    logger.debug(f"Streaming Response Status: {response.status_code}")

                for line in response.iter_lines():
                    if not line:
                        continue

                    # 移除 "data: " 前缀
                    if line.startswith(b"data: "):
                        line = line[6:]

                    # 跳过心跳消息
                    if line.strip() == b"[DONE]":
                        break

                    try:
                        # 解析JSON响应
                        chunk = json.loads(line)

                        # 解析流式响应片段
                        yield self._parse_stream_chunk(chunk)
                    except json.JSONDecodeError as e:
                        logger.error(f"解析流式响应JSON失败: {e}")
                        logger.error(f"原始行: {line}")
                        continue
        except requests.exceptions.RequestException as e:
            logger.error(f"流式请求失败: {e}")
            if hasattr(e, "response") and e.response:
                logger.error(f"响应状态码: {e.response.status_code}")
                logger.error(f"响应内容: {e.response.text}")
            raise

    def _parse_stream_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """解析流式响应片段

        Args:
            chunk: 流式响应片段

        Returns:
            解析后的流式响应片段
        """
        try:
            choices = chunk.get("choices", [])
            if not choices:
                return {"content": "", "tool_calls": []}

            delta = choices[0].get("delta", {})

            # 解析内容
            content = delta.get("content", "")

            # 解析工具调用
            tool_calls = delta.get("tool_calls", [])

            # 构建结果
            result = {
                "content": content,
                "tool_calls": tool_calls,
                "finish_reason": choices[0].get("finish_reason", None),
            }

            return result
        except Exception as e:
            logger.error(f"解析流式响应片段失败: {e}")
            logger.error(f"原始片段: {chunk}")
            return {"content": "", "tool_calls": []}

    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析API响应

        Args:
            response: API响应字典

        Returns:
            解析后的响应字典，包含内容和工具调用信息
        """
        try:
            # 获取响应中的选择
            choices = response.get("choices", [])
            if not choices:
                logger.error("API响应中没有choices字段")
                raise ValueError("API响应格式错误，没有choices字段")

            # 获取第一个选择的消息
            message = choices[0].get("message", {})
            if not message:
                logger.error("API响应中没有message字段")
                raise ValueError("API响应格式错误，没有message字段")

            # 解析内容
            content = message.get("content", "")

            # 解析工具调用
            tool_calls = message.get("tool_calls", [])

            # 构建结果
            result = {"content": content, "tool_calls": tool_calls}

            return result
        except Exception as e:
            logger.error(f"解析API响应失败: {e}")
            logger.error(f"原始响应: {response}")
            raise


# 创建全局LLM客户端实例
_llm_client = None


def get_llm_client() -> LLMClient:
    """获取LLM客户端实例

    Returns:
        LLM客户端实例
    """
    global _llm_client

    if _llm_client is None:
        _llm_client = LLMClient()

    return _llm_client


def send_message(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """发送消息到LLM

    Args:
        messages: 消息列表，包含角色和内容
        model: 模型名称，默认使用配置中的模型
        temperature: 温度参数，控制随机性，默认使用配置中的温度
        max_tokens: 最大生成token数，默认使用配置中的最大token数
        tools: 工具列表，默认为None
        tool_choice: 工具选择，默认为None

    Returns:
        解析后的响应字典，包含内容和工具调用信息
    """
    client = get_llm_client()
    response = client.send_request(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        tools=tools,
        tool_choice=tool_choice,
    )

    return client.parse_response(response)


def send_message_stream(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
):
    """发送消息到LLM并获取流式响应

    Args:
        messages: 消息列表，包含角色和内容
        model: 模型名称，默认使用配置中的模型
        temperature: 温度参数，控制随机性，默认使用配置中的温度
        max_tokens: 最大生成token数，默认使用配置中的最大token数
        tools: 工具列表，默认为None
        tool_choice: 工具选择，默认为None

    Yields:
        流式响应片段，包含内容和工具调用信息
    """
    client = get_llm_client()
    stream_generator = client.send_request(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
        tools=tools,
        tool_choice=tool_choice,
    )

    for chunk in stream_generator:
        yield chunk

    # 移除不需要的返回语句，因为response未定义
    for chunk in stream_generator:
        yield chunk


def parse_json_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """解析JSON格式的响应

    Args:
        response: API响应字典

    Returns:
        解析后的JSON字典
    """
    content = response.get("content", "")

    if not content:
        logger.warning("响应内容为空")
        return {}

    # 增强的预处理逻辑
    try:
        # 使用正则表达式匹配所有代码块
        import re

        json_pattern = re.compile(r"```json(.*?)```", re.DOTALL)
        matches = json_pattern.findall(content)

        if matches:
            # 取最后一个匹配的代码块（防止多次对话干扰）
            content = matches[-1].strip()
        else:
            # 尝试提取可能的JSON部分
            content = content.replace("```json", "").replace("```", "").strip()

        # 处理控制字符
        content = json.dumps(content)[1:-1]  # 转义特殊字符

        # 尝试解析JSON
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"解析JSON失败: {e}")
        logger.error(f"预处理后的内容: {content}")

        # 二次尝试：提取第一个{和最后一个}之间的内容
        try:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_str = content[start : end + 1]
                return json.loads(json_str)
            return {}
        except Exception as e2:
            logger.error(f"二次解析失败: {e2}")
            return {}
