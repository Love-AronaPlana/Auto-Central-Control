#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
memory/conversation.py - 对话记忆模块

该模块负责存储和管理系统与用户的对话历史，提供对话记忆的添加、获取和清除功能。
"""

import os
import json
import time
from datetime import datetime

class ConversationMemory:
    """
    对话记忆类，用于管理系统与用户的对话历史
    """
    
    def __init__(self, max_history=100):
        """
        初始化对话记忆
        
        Args:
            max_history: 最大记忆条目数量
        """
        self.max_history = max_history
        self.conversation_history = []
        self.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 确保memory目录存在
        if not os.path.exists('memory'):
            os.makedirs('memory')
    
    def add_user_message(self, message):
        """
        添加用户消息到对话历史
        
        Args:
            message: 用户消息内容
        """
        self._add_message('user', message)
    
    def add_system_message(self, message):
        """
        添加系统消息到对话历史
        
        Args:
            message: 系统消息内容
        """
        self._add_message('system', message)
    
    def add_agent_message(self, agent_name, message):
        """
        添加特定Agent的消息到对话历史
        
        Args:
            agent_name: Agent名称
            message: 消息内容
        """
        self._add_message(f'agent:{agent_name}', message)
    
    def _add_message(self, role, content):
        """
        添加消息到对话历史的内部方法
        
        Args:
            role: 消息角色
            content: 消息内容
        """
        timestamp = time.time()
        formatted_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        message = {
            'role': role,
            'content': content,
            'timestamp': timestamp,
            'formatted_time': formatted_time
        }
        
        self.conversation_history.append(message)
        
        # 如果超过最大历史记录数，删除最早的记录
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)
        
        # 保存到文件
        self._save_to_file()
    
    def get_conversation_history(self):
        """
        获取完整的对话历史
        
        Returns:
            list: 对话历史列表
        """
        return self.conversation_history
    
    def get_formatted_history(self):
        """
        获取格式化的对话历史，适合提供给AI模型
        
        Returns:
            list: 格式化的对话历史列表
        """
        formatted_history = []
        
        for message in self.conversation_history:
            role = message['role']
            content = message['content']
            
            # 将agent:xxx角色转换为system角色
            if role.startswith('agent:'):
                role = 'system'
            
            formatted_history.append({
                'role': role,
                'content': content
            })
        
        return formatted_history
    
    def clear_history(self):
        """
        清除对话历史
        """
        self.conversation_history = []
        self._save_to_file()
    
    def _save_to_file(self):
        """
        将对话历史保存到文件
        """
        memory_file = os.path.join('memory', f'conversation_{self.session_id}.json')
        
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, session_id=None):
        """
        从文件加载对话历史
        
        Args:
            session_id: 会话ID，如果为None则使用当前会话ID
        
        Returns:
            bool: 是否成功加载
        """
        if session_id:
            self.session_id = session_id
        
        memory_file = os.path.join('memory', f'conversation_{self.session_id}.json')
        
        if os.path.exists(memory_file):
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    self.conversation_history = json.load(f)
                return True
            except Exception as e:
                print(f"加载对话历史出错: {str(e)}")
                return False
        else:
            return False