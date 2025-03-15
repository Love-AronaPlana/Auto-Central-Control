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
        self.api_url = config['api_url']
        self.api_key = config['api_key']
        self.model_name = config['model_name']
        self.max_tokens = config['max_tokens']
        self.debug = config.get('debug', False)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_system_prompt(self) -> str:
        """
        获取系统提示词，子类需要重写此方法
        
        Returns:
            str: 系统提示词
        """
        raise NotImplementedError("子类必须实现get_system_prompt方法")
    
    def call_api(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Dict[str, Any]:
        """
        调用OpenAI API
        
        Args:
            messages: 消息列表，包含角色和内容
            temperature: 温度参数，控制随机性
            
        Returns:
            Dict[str, Any]: API响应
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self.max_tokens
        }
        
        if self.debug:
            self.logger.debug(f"API请求: {json.dumps(data, ensure_ascii=False)}")
        
        try:
            response = requests.post(
                f"{self.api_url}/chat/completions", 
                headers=headers, 
                json=data
            )
            response.raise_for_status()
            result = response.json()
            
            if self.debug:
                self.logger.debug(f"API响应: {json.dumps(result, ensure_ascii=False)}")
            
            return result
        except Exception as e:
            self.logger.error(f"API调用失败: {str(e)}")
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
            content = response['choices'][0]['message']['content']
            # 尝试解析JSON内容
            return json.loads(content)
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