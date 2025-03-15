#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
agent/summary_agent.py - 结束Agent

该模块负责总结所有步骤的执行结果，是工作流的最后一步。
"""

import os
import json
import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent

class SummaryAgent(BaseAgent):
    """
    结束Agent类，负责总结所有步骤的执行结果
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化结束Agent
        
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
        prompt_path = os.path.join('agent', 'prompts', 'summary_agent_prompt.txt')
        
        if os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # 默认提示词
            return """
你是一个专业的总结专家，负责总结所有步骤的执行结果。

你的任务是：
1. 回顾所有已执行的步骤
2. 总结每个步骤的执行结果
3. 提供整体执行情况的概述
4. 指出执行过程中的亮点和不足
5. 给出对未来类似任务的建议

请以JSON格式返回总结结果，格式如下：
{
  "steps_summary": [
    {
      "step_id": 步骤ID,
      "description": "步骤描述",
      "status": "success|partial_success|failed",
      "key_points": ["要点1", "要点2", ...]
    },
    ...
  ],
  "overall_status": "success|partial_success|failed",
  "summary": "整体执行总结",
  "highlights": ["亮点1", "亮点2", ...],
  "issues": ["问题1", "问题2", ...],
  "recommendations": ["建议1", "建议2", ...]
}

记住，你的输出将直接被系统解析为JSON，不要包含任何其他文本。
"""
    
    def process(self, steps: List[Dict[str, Any]], conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理所有步骤的执行结果，生成总结
        
        Args:
            steps: 所有步骤的信息
            conversation_history: 对话历史
            
        Returns:
            Dict[str, Any]: 总结结果
        """
        self.logger.info("开始总结所有步骤的执行结果")
        
        # 构建消息
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"请总结以下所有步骤的执行结果:\n{json.dumps(steps, ensure_ascii=False, indent=2)}\n\n以下是完整的对话历史，可能对你的总结有帮助:\n{json.dumps(conversation_history[-20:], ensure_ascii=False, indent=2)}"}
        ]
        
        # 调用API
        response = self.call_api(messages, temperature=0.4)
        
        # 处理响应
        try:
            summary_result = self.process_response(response)
            self.logger.info("总结完成")
            return summary_result
        except Exception as e:
            self.logger.error(f"总结失败: {str(e)}")
            # 返回一个基本总结结果，避免整个流程中断
            return {
                "steps_summary": [
                    {
                        "step_id": step.get("step_id"),
                        "description": step.get("description", "未知步骤"),
                        "status": "unknown",
                        "key_points": ["无法获取详细信息"]
                    } for step in steps
                ],
                "overall_status": "unknown",
                "summary": f"总结过程出错: {str(e)}",
                "highlights": [],
                "issues": [f"总结过程出错: {str(e)}"],
                "recommendations": ["请检查日志以获取更多信息"]
            }