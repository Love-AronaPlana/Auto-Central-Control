"""Analysis Agent模块

该模块负责分析用户需求，判断是否需要进行任务规划。
"""

import json
import logging
from typing import Dict, Any

from ACC.agent.base import BaseAgent
from ACC.prompt.analysis import ANALYSIS_PROMPT
from ACC.prompt.analysis import FIRST_STEP_PROMPT
from ACC.memory.memory_manager import MemoryManager

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

            # 添加历史对话（修改逻辑，转换自定义角色）
            for msg in history:
                if msg["role"] == "system":
                    # 只在第一次运行时保留系统提示
                    if not any(m["role"] == "system" for m in self.messages):
                        self.messages.append(msg)
                # 将自定义角色转换为API支持的角色
                elif msg["role"] == "analysis_agent":
                    self.messages.append(
                        {"role": "assistant", "content": msg["content"]}
                    )
                elif msg["role"] == "tool_result":
                    # 工具结果作为系统消息
                    self.messages.append(
                        {"role": "system", "content": f"工具执行结果: {msg['content']}"}
                    )
                # 确保所有角色都是API支持的类型
                elif msg["role"] in ["user", "assistant", "system"]:
                    self.messages.append(msg)
                else:
                    # 对于其他不支持的角色，默认转为系统消息
                    self.messages.append(
                        {
                            "role": "assistant",
                            "content": f"{msg['role']}: {msg['content']}",
                        }
                    )

            # 添加当前用户输入
            self.add_message("user", user_input)

            # 发送请求
            try:
                response = self.send_to_llm()
                result = self.parse_json_response(response)
            except Exception as api_error:
                logger.error(f"API请求失败: {str(api_error)}")
                # 提供更友好的错误信息
                return {
                    "message": f"API请求失败，请检查网络连接和API配置。错误详情: {str(api_error)}",
                    "need_planning": False,
                    "complexity": "none",
                    "error": str(api_error),
                }

            # 更新历史记录（保存为assistant角色）
            history_to_save = self.messages.copy()
            if result.get("message"):
                history_to_save.append(
                    {"role": "assistant", "content": result.get("message", "")}
                )
            MemoryManager.save_json("history.json", history_to_save)

            return result

        except Exception as e:
            logger.error(f"分析过程出错: {str(e)}")
            return {
                "message": f"分析过程出错: {str(e)}",
                "need_planning": False,
                "complexity": "none",
            }
