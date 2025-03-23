"""Agent基础类

该模块提供了Agent的基础类，所有Agent都应继承自该类。
Agent负责与LLM交互，执行特定任务。
"""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable, TypeVar

from ACC.llm import send_message, parse_json_response
from ACC.tool.base import ToolRegistry

logger = logging.getLogger(__name__)

# 定义泛型类型变量
T = TypeVar('T')

class BaseAgent(ABC):
    """Agent基础类"""
    
    def __init__(self, name: str, system_prompt: str):
        """初始化Agent
        
        Args:
            name: Agent名称
            system_prompt: 系统提示词
        """
        self.name = name
        self.system_prompt = system_prompt
        self.messages = []
        self.reset_messages()
    
    def reset_messages(self):
        """重置消息列表"""
        self.messages = [
            {"role": "system", "content": self.system_prompt}
        ]
    
    def add_message(self, role: str, content: str):
        """添加消息
        
        Args:
            role: 角色，可以是system、user或assistant
            content: 消息内容
        """
        # 确保角色是有效的
        role = self._ensure_valid_role(role, content)
        self.messages.append({"role": role, "content": content})
    
    def _ensure_valid_role(self, role: str, content: str) -> str:
        """确保角色是有效的
        
        Args:
            role: 原始角色
            content: 消息内容
            
        Returns:
            有效的角色（system、user或assistant）
        """
        valid_roles = ["system", "user", "assistant"]
        
        if role in valid_roles:
            return role
        else:
            # 对于不支持的角色，转换为user角色
            logger.warning(f"[{self.name}] 不支持的角色类型 '{role}'，已转换为 'user'")
            return "user"
    
    def normalize_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """规范化消息列表，确保所有消息角色都是有效的
        
        Args:
            messages: 原始消息列表
            
        Returns:
            规范化后的消息列表
        """
        normalized = []
        for msg in messages:
            if not isinstance(msg, dict):
                continue
                
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            valid_role = self._ensure_valid_role(role, content)
            
            # 如果角色被转换，为内容添加原始角色前缀
            if valid_role != role and valid_role == "system":
                content = f"{role}: {content}"
                
            normalized.append({"role": valid_role, "content": content})
            
        return normalized
    
    def get_tools_dict(self) -> List[Dict[str, Any]]:
        """获取工具字典列表
        
        Returns:
            工具字典列表
        """
        return ToolRegistry.get_tools_dict()
    
    def retry_operation(self, func: Callable[..., T], *args, **kwargs) -> T:
        """重试操作装饰器
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            Exception: 如果重试三次后仍然失败，则抛出最后一次的异常
        """
        max_retries = 5
        retry_delay = 30  # 秒
        request_timeout = 180  # 3分钟超时时间
        
        for attempt in range(1, max_retries + 1):
            try:
                # 添加超时控制
                import threading
                import concurrent.futures
                
                # 使用线程池执行函数，设置超时时间
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(func, *args, **kwargs)
                    try:
                        return future.result(timeout=request_timeout)
                    except concurrent.futures.TimeoutError:
                        # 请求超时，取消任务并抛出异常
                        logger.warning(f"[{self.name}] 请求超时 (超过 {request_timeout} 秒)")
                        # 尝试取消正在执行的任务
                        for t in threading.enumerate():
                            if t.name.startswith('ThreadPoolExecutor'):
                                # 这里无法直接终止线程，但会在下一次循环中重新创建线程池
                                pass
                        raise TimeoutError(f"请求超时 (超过 {request_timeout} 秒)")
                        
            except Exception as e:
                logger.warning(f"[{self.name}] 操作失败 (尝试 {attempt}/{max_retries}): {str(e)}")
                
                if attempt < max_retries:
                    logger.info(f"[{self.name}] 等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"[{self.name}] 重试 {max_retries} 次后仍然失败")
                    raise
    
    @abstractmethod
    def run(self, user_input: str) -> Dict[str, Any]:
        """运行Agent
        
        Args:
            user_input: 用户输入
            
        Returns:
            运行结果字典
        """
        pass
    
    def send_to_llm(self, tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """发送消息到LLM
        
        Args:
            tools: 工具列表，默认为None
            
        Returns:
            LLM响应字典
        """
        # 在发送前规范化消息
        normalized_messages = self.normalize_messages(self.messages)
        
        # 获取当前配置的max_tokens
        from ACC.config import get_llm_config
        config = get_llm_config()
        max_tokens = config.get('max_tokens', None)
        
        # 始终发送max_tokens参数
        kwargs = {
            'messages': normalized_messages, 
            'tools': tools,
            'max_tokens': max_tokens
        }
            
        return self.retry_operation(send_message, **kwargs)
    
    def parse_json_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析JSON格式的响应
        
        Args:
            response: LLM响应字典
            
        Returns:
            解析后的JSON字典
        """
        return self.retry_operation(parse_json_response, response)
