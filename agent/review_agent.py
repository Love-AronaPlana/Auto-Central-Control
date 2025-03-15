#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
agent/review_agent.py - 复查Agent

该模块负责检查执行Agent的执行结果，发现可能的错误，是工作流的第四步。
"""

import os
import json
import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent

class ReviewAgent(BaseAgent):
    """
    复查Agent类，负责检查执行Agent的执行结果
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化复查Agent
        
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
        prompt_path = os.path.join('agent', 'prompts', 'review_agent_prompt.txt')
        
        if os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # 默认提示词
            return """
你是一个专业的质量检查专家，负责检查执行Agent的执行结果，发现可能的错误。

你的任务是：
1. 仔细检查执行结果中的每个操作
2. 将执行结果与原始步骤要求进行对比
3. 识别执行过程中可能出现的错误或问题
4. 确定是否需要修复
5. 如果需要修复，提供详细的错误信息和位置

请以JSON格式返回检查结果，格式如下：
{
  "step_id": 检查的步骤ID,
  "has_errors": true|false,
  "errors": [
    {
      "error_id": 1,
      "operation_id": 相关操作ID,
      "error_type": "错误类型",
      "description": "错误描述",
      "location": "错误位置",
      "severity": "high|medium|low"
    },
    ...
  ],
  "review_summary": "检查总结"
}

记住，你的输出将直接被系统解析为JSON，不要包含任何其他文本。
"""
    
    def process(self, execution_result: Dict[str, Any], original_step: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理执行结果，检查是否有错误
        
        Args:
            execution_result: 执行Agent的执行结果
            original_step: 原始步骤信息
            conversation_history: 对话历史
            
        Returns:
            Dict[str, Any]: 检查结果
        """
        step_id = execution_result.get('step_id')
        self.logger.info(f"开始检查步骤 {step_id} 的执行结果")
        
        # 构建消息
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"请检查以下执行结果是否符合原始步骤要求，并发现可能的错误:\n\n原始步骤:\n{json.dumps(original_step, ensure_ascii=False, indent=2)}\n\n执行结果:\n{json.dumps(execution_result, ensure_ascii=False, indent=2)}\n\n以下是之前的对话历史，可能对你的检查有帮助:\n{json.dumps(conversation_history[-5:], ensure_ascii=False, indent=2)}"}
        ]
        
        # 调用API
        response = self.call_api(messages, temperature=0.2)
        
        # 处理响应
        try:
            review_result = self.process_response(response)
            self.logger.info(f"步骤 {step_id} 检查完成，{'发现错误' if review_result.get('has_errors', False) else '未发现错误'}")
            return review_result
        except Exception as e:
            self.logger.error(f"检查执行结果失败: {str(e)}")
            # 返回一个基本检查结果，避免整个流程中断
            return {
                "step_id": step_id,
                "has_errors": False,
                "errors": [],
                "review_summary": f"检查过程出错: {str(e)}"
            }