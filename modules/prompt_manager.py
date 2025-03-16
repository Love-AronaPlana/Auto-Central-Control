#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
提示词管理模块
负责管理系统提示词和用户提示词
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

# 获取日志记录器
logger = logging.getLogger("ACC")

class PromptManager:
    """
    提示词管理类
    负责加载和管理系统提示词和用户提示词
    """
    
    def __init__(self):
        """
        初始化提示词管理器
        """
        self.prompts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'prompts')
        self.system_prompt_file = os.path.join(self.prompts_dir, 'system.txt')
        self.user_prompts_file = os.path.join(self.prompts_dir, 'user_prompts.json')
        self.current_prompt_index = 0
        self.user_prompts = []
        
        # 确保提示词目录存在
        if not os.path.exists(self.prompts_dir):
            os.makedirs(self.prompts_dir)
        
        # 加载用户提示词
        self._load_user_prompts()
        
        logger.info("初始化提示词管理器")
    
    def _load_user_prompts(self) -> None:
        """
        加载用户提示词
        """
        if os.path.exists(self.user_prompts_file):
            try:
                with open(self.user_prompts_file, 'r', encoding='utf-8') as f:
                    self.user_prompts = json.load(f)
                logger.info(f"已加载{len(self.user_prompts)}条用户提示词")
            except Exception as e:
                logger.error(f"加载用户提示词出错: {e}")
                self.user_prompts = []
        else:
            # 创建默认的用户提示词文件
            default_prompts = [
                "请分析当前任务并提供解决方案。",
                "请继续执行当前任务。"
            ]
            self.user_prompts = default_prompts
            self._save_user_prompts()
    
    def _save_user_prompts(self) -> None:
        """
        保存用户提示词
        """
        try:
            with open(self.user_prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_prompts, f, ensure_ascii=False, indent=4)
            logger.info(f"已保存{len(self.user_prompts)}条用户提示词")
        except Exception as e:
            logger.error(f"保存用户提示词出错: {e}")
    
    def get_system_prompt(self) -> str:
        """
        获取系统提示词
        
        Returns:
            系统提示词内容
        """
        if os.path.exists(self.system_prompt_file):
            try:
                with open(self.system_prompt_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"读取系统提示词出错: {e}")
        
        # 如果系统提示词文件不存在，创建默认的系统提示词
        default_system_prompt = """你是一个智能AI助手，你的任务是帮助用户解决问题。
请以JSON格式回复，确保你的回复可以被解析为有效的JSON对象。"""
        
        try:
            with open(self.system_prompt_file, 'w', encoding='utf-8') as f:
                f.write(default_system_prompt)
            logger.info("已创建默认系统提示词")
        except Exception as e:
            logger.error(f"创建系统提示词出错: {e}")
        
        return default_system_prompt
    
    def get_current_prompt(self) -> Optional[str]:
        """
        获取当前提示词
        
        Returns:
            当前提示词内容，如果没有则返回None
        """
        if not self.user_prompts or self.current_prompt_index >= len(self.user_prompts):
            return None
        
        prompt = self.user_prompts[self.current_prompt_index]
        self.current_prompt_index += 1
        
        return prompt
    
    def should_continue(self) -> bool:
        """
        检查是否应该继续循环
        
        Returns:
            是否应该继续循环
        """
        # 如果还有未使用的提示词，则继续循环
        return self.current_prompt_index < len(self.user_prompts)
    
    def add_prompt(self, prompt: str) -> None:
        """
        添加用户提示词
        
        Args:
            prompt: 提示词内容
        """
        self.user_prompts.append(prompt)
        self._save_user_prompts()
        
    def reset(self) -> None:
        """
        重置提示词管理器
        """
        self.current_prompt_index = 0