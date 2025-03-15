#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
agent/fix_agent.py - 修复Agent

该模块负责修复复查Agent发现的错误，是工作流的第五步。
"""

import os
import json
import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent

class FixAgent(BaseAgent):
    """
    修复Agent类，负责修复复查Agent发现的错误
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化修复Agent
        
        Args:
            config: 系统配置信息
        """
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_system_prompt(self) -> str:
        """
        获取系统提示词
        
        Returns:
            str: 系统提示词
        """
        prompt_path = os.path.join('agent', 'prompts', 'fix_agent_prompt.txt')
        
        if os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # 默认提示词
            return """
你是一个专业的错误修复专家，负责修复复查Agent发现的错误。

你的任务是：
1. 仔细分析复查Agent发现的错误
2. 确定错误的根本原因
3. 设计修复方案
4. 执行修复操作
5. 确保修复不会引入新的问题

请以JSON格式返回修复结果，格式如下：
{
  "step_id": 修复的步骤ID,
  "fixed_errors": [
    {
      "error_id": 修复的错误ID,
      "fix_description": "修复描述",
      "fix_method": "修复方法"
    },
    ...
  ],
  "execution_results": [
    {
      "operation_id": 操作ID,
      "status": "success|failed",
      "result": "执行结果",
      "error": "如果失败，错误信息"
    },
    ...
  ],
  "overall_status": "success|partial_success|failed",
  "summary": "修复总结"
}

记住，你的输出将直接被系统解析为JSON，不要包含任何其他文本。
"""
    
    def process(self, review_result: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理复查结果，修复错误
        
        Args:
            review_result: 复查Agent的检查结果
            conversation_history: 对话历史
            
        Returns:
            Dict[str, Any]: 修复结果
        """
        step_id = review_result.get('step_id')
        errors = review_result.get('errors', [])
        
        self.logger.info(f"开始修复步骤 {step_id} 的错误，共 {len(errors)} 个错误")
        
        # 如果没有错误，直接返回
        if not errors:
            self.logger.info(f"步骤 {step_id} 没有需要修复的错误")
            return {
                "step_id": step_id,
                "fixed_errors": [],
                "execution_results": [],
                "overall_status": "success",
                "summary": "没有需要修复的错误"
            }
        
        # 构建消息
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"请修复以下错误:\n{json.dumps(review_result, ensure_ascii=False, indent=2)}\n\n以下是之前的对话历史，可能对你的修复有帮助:\n{json.dumps(conversation_history[-10:], ensure_ascii=False, indent=2)}"}
        ]
        
        # 调用API
        response = self.call_api(messages, temperature=0.3)
        
        # 处理响应
        try:
            fix_result = self.process_response(response)
            self.logger.info(f"步骤 {step_id} 修复完成，状态: {fix_result.get('overall_status', 'unknown')}")
            return fix_result
        except Exception as e:
            self.logger.error(f"修复错误失败: {str(e)}")
            # 返回一个基本修复结果，避免整个流程中断
            return {
                "step_id": step_id,
                "fixed_errors": [],
                "execution_results": [],
                "overall_status": "failed",
                "summary": f"修复过程出错: {str(e)}"
            }