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

from ASN.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class PlanningAgent(BaseAgent):
    """规划Agent，负责分析用户需求并创建详细的执行计划"""

    def __init__(self):
        """初始化规划Agent"""
        super().__init__(name="planning", system_prompt=SYSTEM_PROMPT)
        logger.info("规划Agent初始化完成")

    def parse_json_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """专用JSON解析方法"""
        try:
            content = response.get("content", "").replace("\x00", "").strip()

            # 加强代码块去除逻辑（支持```json和```）
            cleaned = re.sub(r"^```(json)?|```$", "", content, flags=re.MULTILINE)

            # 处理中文引号问题
            cleaned = cleaned.replace("“", '"').replace("”", '"')

            return json.loads(cleaned, strict=False)
        except Exception as e:
            # 添加详细错误日志
            logger.error(f"规划结果解析失败: {str(e)}\n原始内容: {content[:500]}...")
            return {"error": f"JSON解析错误: {str(e)}", "raw_response": content}

    def run(self, user_input: str) -> Dict[str, Any]:
        """运行规划Agent"""
        logger.info(f"规划Agent开始处理用户输入: {user_input}")

        try:
            self.reset_messages()
            self.add_message("user", FIRST_STEP_PROMPT.format(user_input=user_input))

            logger.info("🔄 正在向LLM发送规划请求...")
            response = self.send_to_llm()
            logger.info("✅ 成功接收LLM规划响应")

            planning_result = self.parse_json_response(response)

            # 修复任务结构访问方式（兼容tasks为字典或列表的情况）
            tasks = planning_result.get("tasks", {})
            if isinstance(tasks, list) and len(tasks) > 0:
                tasks = tasks[0]
            if task_structure := tasks.get("task_structure"):
                MemoryManager.save_planning_md(task_structure)

            self.reset_messages()
            return planning_result
        except Exception as e:
            self.reset_messages()
            logger.error(f"规划流程失败: {e}")
            return {
                "error": f"规划流程失败: {str(e)}",
                "raw_response": response.get("content", ""),
            }
