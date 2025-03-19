"""Agent基础类

该模块提供了Agent的基础类，所有Agent都应继承自该类。
Agent负责与LLM交互，执行特定任务。
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union

from ASN.llm import send_message, parse_json_response
from ASN.tool.base import ToolRegistry

logger = logging.getLogger(__name__)

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
        self.messages.append({"role": role, "content": content})
    
    def get_tools_dict(self) -> List[Dict[str, Any]]:
        """获取工具字典列表
        
        Returns:
            工具字典列表
        """
        return ToolRegistry.get_tools_dict()
    
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
        return send_message(messages=self.messages, tools=tools)
    
    def parse_json_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析JSON格式的响应
        
        Args:
            response: LLM响应字典
            
        Returns:
            解析后的JSON字典
        """
        return parse_json_response(response)
