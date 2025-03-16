#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
agent/step_agent.py - 步骤Agent

该模块负责将用户需求分解为详细的执行步骤，是工作流的第一步。
"""

import os
import json
import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent


class StepAgent(BaseAgent):
    """
    步骤Agent类，负责将用户需求分解为详细的执行步骤
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化步骤Agent

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
        prompt_path = os.path.join("agent", "prompts", "step_agent_prompt.txt")

        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            # 默认提示词
            return """
你是一个专业的任务分解专家，负责将用户的需求分解为详细的执行步骤。

你的任务是：
1. 仔细分析用户的需求
2. 将需求分解为清晰、具体、可执行的步骤
3. 确保步骤的逻辑顺序正确
4. 每个步骤应该足够具体，便于后续Agent执行
5. 考虑可能的边界情况和异常情况

请以JSON格式返回分解后的步骤，格式如下：
[
  {
    "step_id": 1,
    "description": "步骤简短描述",
    "details": "步骤详细说明，包括需要考虑的要点",
    "expected_outcome": "预期完成后的结果"
  },
  ...
]

记住，你的输出将直接被系统解析为JSON，不要包含任何其他文本。
"""

    def process(self, user_input: str) -> List[Dict[str, Any]]:
        """
        处理用户输入，将需求分解为详细步骤

        Args:
            user_input: 用户输入的需求文本

        Returns:
            List[Dict[str, Any]]: 分解后的步骤列表
        """
        self.logger.info("开始分解用户需求为详细步骤")

        # 构建消息
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": user_input},
        ]

        # 调用API
        response = self.call_api(messages, temperature=0.5)

        # 处理响应
        try:
            steps = self.process_response(response)
            self.logger.info(f"成功分解用户需求为{len(steps)}个步骤")
            return steps
        except Exception as e:
            self.logger.error(f"分解用户需求失败: {str(e)}")
            # 返回一个基本步骤，避免整个流程中断
            return [
                {
                    "step_id": 1,
                    "description": "执行用户请求",
                    "details": user_input,
                    "expected_outcome": "完成用户请求",
                }
            ]
