#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
agent/analysis_agent.py - 分析Agent

该模块负责分析如何执行当前步骤，是工作流的第二步。
"""

import os
import json
import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent


class AnalysisAgent(BaseAgent):
    """
    分析Agent类，负责分析如何执行当前步骤
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化分析Agent

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
        prompt_path = os.path.join("agent", "prompts", "analysis_agent_prompt.txt")

        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            # 默认提示词
            return """
你是一个专业的任务分析专家，负责分析如何执行当前步骤。

你的任务是：
1. 仔细分析当前步骤的需求和上下文
2. 确定执行该步骤所需的具体操作
3. 考虑可能的实现方法和工具
4. 提供详细的执行计划
5. 考虑可能的边界情况和异常情况

请以JSON格式返回执行计划，格式如下：
{
  "step_id": 当前步骤ID,
  "analysis": "对当前步骤的分析",
  "execution_plan": {
    "operations": [
      {
        "operation_id": 1,
        "operation_type": "操作类型",
        "description": "操作描述",
        "parameters": {操作所需参数},
        "expected_outcome": "预期结果"
      },
      ...
    ],
    "tools_required": ["工具1", "工具2", ...],
    "potential_issues": ["可能的问题1", "可能的问题2", ...],
    "fallback_plan": "如果主要计划失败，应该如何处理"
  }
}

记住，你的输出将直接被系统解析为JSON，不要包含任何其他文本。
"""

    def process(
        self, current_step: Dict[str, Any], conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        处理当前步骤，分析如何执行

        Args:
            current_step: 当前需要执行的步骤信息
            conversation_history: 对话历史

        Returns:
            Dict[str, Any]: 执行计划
        """
        self.logger.info(
            f"开始分析步骤 {current_step['step_id']}: {current_step['description']}"
        )

        # 构建消息
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {
                "role": "user",
                "content": f"请分析如何执行以下步骤:\n{json.dumps(current_step, ensure_ascii=False, indent=2)}\n\n以下是之前的对话历史，可能对你的分析有帮助:\n{json.dumps(conversation_history[-10:], ensure_ascii=False, indent=2)}",
            },
        ]

        # 调用API
        response = self.call_api(messages, temperature=0.3)

        # 处理响应
        try:
            execution_plan = self.process_response(response)
            self.logger.info(f"成功分析步骤 {current_step['step_id']}")
            return execution_plan
        except Exception as e:
            self.logger.error(f"分析步骤失败: {str(e)}")
            # 返回一个基本执行计划，避免整个流程中断
            return {
                "step_id": current_step["step_id"],
                "analysis": f"无法分析步骤: {str(e)}",
                "execution_plan": {
                    "operations": [
                        {
                            "operation_id": 1,
                            "operation_type": "manual",
                            "description": current_step["details"],
                            "parameters": {},
                            "expected_outcome": current_step["expected_outcome"],
                        }
                    ],
                    "tools_required": [],
                    "potential_issues": ["分析失败，可能无法正确执行"],
                    "fallback_plan": "请手动执行该步骤",
                },
            }
