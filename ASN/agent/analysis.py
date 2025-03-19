"""Analysis Agent模块

该模块负责分析用户需求，判断是否需要进行任务规划。
"""

import json
import logging
from typing import Dict, Any

from ASN.agent.base import BaseAgent
from ASN.prompt.analysis import ANALYSIS_PROMPT
from ASN.prompt.planning import FIRST_STEP_PROMPT
from ASN.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class AnalysisAgent(BaseAgent):
    """分析代理类，负责分析用户需求是否需要规划"""

    def __init__(self):
        """初始化分析代理"""
        super().__init__(name="Analysis Agent", system_prompt=ANALYSIS_PROMPT)
        logger.info("初始化分析代理")

    def run(self, user_input: str) -> Dict[str, Any]:
        """运行分析代理"""
        logger.info(f"开始分析用户需求: {user_input}")

        try:
            # 读取历史记录（新增）
            history = MemoryManager.read_json("history.json")

            # 构建消息上下文（重要修改）
            self.reset_messages()

            # 添加历史对话（新增逻辑）
            for msg in history:
                if msg["role"] == "system":
                    # 只在第一次运行时保留系统提示
                    if not any(m["role"] == "system" for m in self.messages):
                        self.messages.append(msg)
                else:
                    self.messages.append(msg)

            # 添加当前用户输入（保留原有逻辑）
            self.add_message("user", user_input)

            # 发送给LLM前的处理（新增格式化）
            formatted_messages = [
                {
                    "role": m["role"],
                    "content": (
                        FIRST_STEP_PROMPT.format(user_input=m["content"])
                        if m["role"] == "user"
                        else m["content"]
                    ),
                }
                for m in self.messages
            ]

            # 发送请求（修改为使用格式化后的消息）
            response = self.send_to_llm(formatted_messages)
            result = self.parse_json_response(response)

            # 更新历史记录（保留原有逻辑）
            MemoryManager.save_json(
                "history.json",
                self.messages
                + [{"role": "analysis_agent", "content": result.get("message", "")}],
            )

            return result

        except Exception as e:
            logger.error(f"分析过程出错: {str(e)}")
            return {
                "message": f"分析过程出错: {str(e)}",
                "need_planning": False,
                "complexity": "none",
            }
