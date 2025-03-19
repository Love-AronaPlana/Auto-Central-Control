"""规划Agent模块

该模块提供了规划Agent的实现，负责分析用户需求并创建详细的执行计划。
规划Agent是ASN系统的核心组件之一，它将用户的需求转化为可执行的任务列表。
"""

import json
import logging
import re

from typing import Dict, Any

from ASN.agent.base import BaseAgent
from ASN.prompt.planning import SYSTEM_PROMPT, FIRST_STEP_PROMPT

logger = logging.getLogger(__name__)


class PlanningAgent(BaseAgent):
    """规划Agent，负责分析用户需求并创建详细的执行计划"""

    def __init__(self):
        """初始化规划Agent"""
        super().__init__(name="planning", system_prompt=SYSTEM_PROMPT)
        logger.info("规划Agent初始化完成")

    def run(self, user_input: str) -> Dict[str, Any]:
        """运行规划Agent

        Args:
            user_input: 用户输入

        Returns:
            规划结果字典
        """
        logger.info(f"规划Agent开始处理用户输入: {user_input}")

        try:
            # 单次会话管理
            self.reset_messages()
            self.add_message("user", FIRST_STEP_PROMPT.format(user_input=user_input))

            logger.info("🔄 正在向LLM发送规划请求...")
            response = self.send_to_llm()
            logger.info("✅ 成功接收LLM规划响应")

            planning_result = self.parse_json_response(response)
            self.reset_messages()  # 立即重置会话
            return planning_result
        except Exception as e:
            self.reset_messages()  # 异常时也重置会话
            logger.error(f"规划流程失败: {e}")
            return {
                "error": f"规划流程失败: {str(e)}",
                "raw_response": response.get("content", ""),
            }

    def parse_json_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """专用JSON解析方法"""
        try:
            # 清理非法控制字符并提取JSON内容
            content = response.get("content", "").replace("\x00", "").strip()

            # 去除可能的代码块标记
            cleaned = re.sub(r"^```json\s*|\s*```$", "", content, flags=re.DOTALL)

            # 处理转义字符
            cleaned = cleaned.replace('\\"', '"').replace("\\n", "\n").strip()

            return json.loads(cleaned, strict=False)
        except json.JSONDecodeError as e:
            logger.error(f"规划结果解析失败: {e}\n原始内容: {content}")
            return {"error": f"Invalid JSON format: {str(e)}", "raw_response": content}
