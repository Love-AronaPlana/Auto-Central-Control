"""Analysis Agent模块

该模块负责分析用户需求，判断是否需要进行任务规划。
"""

import json
import logging
from typing import Dict, Any

from ASN.agent.base import BaseAgent
from ASN.prompt.analysis import ANALYSIS_PROMPT
from ASN.prompt.planning import FIRST_STEP_PROMPT

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

            self.reset_messages()
            self.add_message("user", FIRST_STEP_PROMPT.format(user_input=user_input))

            logger.info("🔄 正在向LLM发送分析请求...")
            response = self.send_to_llm()

            # 解析响应（保持原有逻辑）
            result = self.parse_json_response(response)
            return result

        except Exception as e:
            logger.error(f"分析过程出错: {str(e)}")
            # 修改异常返回结构以匹配新提示词格式
            return {
                "message": f"分析过程出错: {str(e)}",
                "need_planning": False,
                "complexity": "none",  # 出错时标记为无需规划
            }
