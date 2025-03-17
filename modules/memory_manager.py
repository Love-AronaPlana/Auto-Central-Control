#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
记忆管理模块
负责管理对话历史记录
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# 获取日志记录器
logger = logging.getLogger("ACC")

class MemoryManager:
    """
    记忆管理类
    负责管理对话历史记录
    """
    
    def __init__(self, session_id: str):
        self.conversation_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "memory",
            f"conversation_{session_id}.json"
        )
        self.system_prompt_added = False  # 新增状态标志

    def init_conversation(self, system_prompt: str) -> List[Dict[str, Any]]:
        """
        初始化对话历史时添加系统提示
        """
        conversation = []
        if system_prompt:  # 添加系统提示到对话历史
            conversation.append({
                "role": "system",
                "content": system_prompt
            })
        self.save_conversation(conversation)
        return conversation

    def load_conversation(self) -> List[Dict[str, Any]]:
        """加载时自动标记系统提示已添加"""
        if os.path.exists(self.conversation_file):
            try:
                with open(self.conversation_file, 'r', encoding='utf-8') as f:
                    conversation = json.load(f)
                    if any(msg.get("role") == "system" for msg in conversation):
                        self.system_prompt_added = True
                return conversation
            except Exception as e:
                logger.error(f"加载对话历史出错: {e}")
        return []

    def save_conversation(self, conversation: List[Dict[str, Any]]) -> None:
        """
        保存对话历史
        
        Args:
            conversation: 对话历史列表
        """
        try:
            with open(self.conversation_file, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, ensure_ascii=False, indent=4)
            logger.debug(f"已保存对话历史，共{len(conversation)}条消息")
        except Exception as e:
            logger.error(f"保存对话历史出错: {e}")
    
    def load_conversation(self) -> List[Dict[str, Any]]:
        """
        加载对话历史
        
        Returns:
            对话历史列表
        """
        if not os.path.exists(self.conversation_file):
            return []
        
        try:
            with open(self.conversation_file, 'r', encoding='utf-8') as f:
                conversation = json.load(f)
            logger.debug(f"已加载对话历史，共{len(conversation)}条消息")
            return conversation
        except Exception as e:
            logger.error(f"加载对话历史出错: {e}")
            return []
    
    def clear_conversation(self) -> None:
        """
        清空对话历史
        """
        if os.path.exists(self.conversation_file):
            try:
                os.remove(self.conversation_file)
                logger.info("已清空对话历史")
            except Exception as e:
                logger.error(f"清空对话历史出错: {e}")
        
        # 重新初始化对话历史
        self.init_conversation()