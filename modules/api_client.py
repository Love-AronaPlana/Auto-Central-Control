# API客户端模块

import json
import requests
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from config.system_config import get_config
from config.logging_config import get_logger
from config.constants import SYSTEM_ROLE, USER_ROLE, ASSISTANT_ROLE

# 获取日志记录器
logger = get_logger(__name__)


class ApiClient:
    """OpenAI API客户端

    负责与OpenAI API进行通信，发送请求并获取响应。
    支持流式输出和完整响应两种模式。
    """

    def __init__(self):
        """初始化API客户端"""
        config = get_config()
        self.api_url = config["api_url"]
        self.api_key = config["api_key"]
        self.model = config["model"]
        self.max_tokens = config["max_tokens"]
        self.temperature = config["temperature"]

        # 检查API密钥
        if not self.api_key or self.api_key == "your_api_key_here":
            logger.error("API密钥未设置，请在.env文件中设置API_KEY")
            raise ValueError("API密钥未设置，请在.env文件中设置API_KEY")

    def _prepare_headers(self) -> Dict[str, str]:
        """准备请求头

        Returns:
            Dict[str, str]: 请求头字典
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _prepare_messages(
        self, system_prompt: str, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """准备消息列表

        Args:
            system_prompt (str): 系统提示词
            messages (List[Dict[str, str]]): 消息历史

        Returns:
            List[Dict[str, str]]: 准备好的消息列表
        """
        # 确保系统提示词在最前面
        prepared_messages = [{"role": SYSTEM_ROLE, "content": system_prompt}]

        # 添加历史消息
        for message in messages:
            if message["role"] not in [SYSTEM_ROLE, USER_ROLE, ASSISTANT_ROLE]:
                logger.warning(f"未知的消息角色: {message['role']}，将被忽略")
                continue
            prepared_messages.append(message)

        return prepared_messages

    def _prepare_payload(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """准备请求负载

        Args:
            system_prompt (str): 系统提示词
            messages (List[Dict[str, str]]): 消息历史
            functions (Optional[List[Dict[str, Any]]], optional): 函数定义列表

        Returns:
            Dict[str, Any]: 请求负载字典
        """
        payload = {
            "model": self.model,
            "messages": self._prepare_messages(system_prompt, messages),
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        # 如果有函数定义，添加到负载中
        if functions:
            payload["functions"] = functions
            payload["function_call"] = "auto"

        return payload

    def send_request(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """发送请求并获取完整响应

        Args:
            system_prompt (str): 系统提示词
            messages (List[Dict[str, str]]): 消息历史
            functions (Optional[List[Dict[str, Any]]], optional): 函数定义列表

        Returns:
            Dict[str, Any]: API响应
        """
        try:
            headers = self._prepare_headers()
            payload = self._prepare_payload(system_prompt, messages, functions)

            # 发送请求
            response = requests.post(
                f"{self.api_url}/chat/completions", headers=headers, json=payload
            )

            # 检查响应状态
            response.raise_for_status()

            # 解析响应
            result = response.json()
            logger.info("成功获取API响应")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            return {"error": str(e)}
        except json.JSONDecodeError as e:
            logger.error(f"解析API响应失败: {str(e)}")
            return {"error": f"解析API响应失败: {str(e)}"}
        except Exception as e:
            logger.error(f"发送请求时出错: {str(e)}")
            return {"error": str(e)}

    async def send_request_stream(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        try:
            headers = self._prepare_headers()
            payload = self._prepare_payload(system_prompt, messages, functions)

            # 记录请求内容（使用结构化日志）
            logger.info(
                "API Request:\n%s", json.dumps(payload, indent=2, ensure_ascii=False)
            )

            payload["stream"] = True

            full_response = ""
            function_call = None

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/chat/completions", headers=headers, json=payload
                ) as response:
                    # 检查响应状态
                    response.raise_for_status()

                    # 处理流式响应
                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break

                            try:
                                chunk = json.loads(data)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})

                                # 处理内容
                                if "content" in delta and delta["content"]:
                                    content = delta["content"]
                                    full_response += content
                                    if callback:
                                        await callback(content)

                                # 处理函数调用
                                if "function_call" in delta:
                                    if function_call is None:
                                        function_call = {"name": "", "arguments": ""}

                                    if "name" in delta["function_call"]:
                                        function_call["name"] = delta["function_call"][
                                            "name"
                                        ]

                                    if "arguments" in delta["function_call"]:
                                        function_call["arguments"] += delta[
                                            "function_call"
                                        ]["arguments"]

                            except json.JSONDecodeError:
                                continue

            # 构建最终响应
            result = {
                "choices": [
                    {
                        "message": {
                            "role": ASSISTANT_ROLE,
                            "content": full_response if not function_call else None,
                            "function_call": function_call,
                        }
                    }
                ]
            }

            logger.info("成功获取流式API响应")
            # 处理完成后记录完整响应
            logger.info(
                "API Response:\n%s", json.dumps(result, indent=2, ensure_ascii=False)
            )

            return result

        except aiohttp.ClientError as e:
            logger.error(f"流式API请求失败: {str(e)}")
            return {"error": str(e)}
        except json.JSONDecodeError as e:
            logger.error(f"解析流式API响应失败: {str(e)}")
            return {"error": f"解析流式API响应失败: {str(e)}"}
        except Exception as e:
            logger.error(f"发送流式请求时出错: {str(e)}")
            return {"error": str(e)}
