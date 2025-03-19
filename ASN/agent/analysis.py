"""Analysis Agent模块

该模块负责分析用户需求，判断是否需要进行任务规划。
"""

import json
import logging
from typing import Dict, Any

from ASN.agent.base import BaseAgent
from ASN.prompt.analysis import ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

class AnalysisAgent(BaseAgent):
    """分析代理类，负责分析用户需求是否需要规划"""
    
    def __init__(self):
        """初始化分析代理"""
        super().__init__(
            name="Analysis Agent",
            system_prompt=ANALYSIS_PROMPT
        )
        logger.info("初始化分析代理")
    
    def run(self, user_input: str) -> Dict[str, Any]:
        """运行分析代理
        
        Args:
            user_input: 用户输入
            
        Returns:
            分析结果字典
        """
        logger.info(f"开始分析用户需求: {user_input}")
        
        try:
            # 添加用户输入到消息列表
            self.add_message("user", f"分析需求：{user_input}\n请判断是否需要任务规划")
        
            logger.info("🔄 正在向LLM发送分析请求...")
            response = self.send_to_llm()
            logger.info("✅ 成功接收LLM分析响应")
            
            # 解析响应
            result = self.parse_json_response(response)
            return result
            
        except Exception as e:
            logger.error(f"分析过程出错: {str(e)}")
            return {
                "need_planning": False,
                "reason": f"分析过程出错: {str(e)}",
                "complexity": "medium"
            }
