"""ASN工作流程控制模块

该模块负责控制ASN系统的主要工作流程，包括：
- 初始化系统组件
- 协调各个Agent的工作
- 处理执行结果
- 管理系统状态
"""

import json
import logging
import os
from typing import Dict, Any

from ASN.agent.planning import PlanningAgent
from ASN.agent.analysis import AnalysisAgent
from ASN.memory.memory_manager import MemoryManager
from ASN.agent.ordinary_reply import OrdinaryReplyAgent

logger = logging.getLogger(__name__)

from ASN.agent.ordinary_reply import OrdinaryReplyAgent

# 在顶部添加导入
from ASN.agent.refinement import RefinementAgent


class Workflow:
    """ASN工作流程控制类"""

    def __init__(self):
        """初始化工作流程控制器"""
        logger.info("初始化工作流程控制器")

        # 清空TODO目录
        MemoryManager.clean_todo_directory()

        MemoryManager.clean_refinement_directory()

        # 初始化Agent
        self.analysis_agent = AnalysisAgent()
        self.planning_agent = PlanningAgent()
        self.refinement_agent = RefinementAgent()  # 新增细化Agent
        self.ordinary_reply_agent = OrdinaryReplyAgent()

        # 确保必要的目录存在
        self._ensure_directories()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        dirs = ["logs", "memory", "examples"]
        for dir_name in dirs:
            dir_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), dir_name
            )
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"创建目录: {dir_path}")

    def execute(self, user_input: str) -> Dict[str, Any]:
        """执行工作流程"""
        while True:
            if user_input.strip().lower() in ("exit", "退出"):
                return {"status": "exit", "message": "用户请求退出系统"}

            logger.info(f"开始执行工作流程，用户输入: {user_input}")

            try:
                # 1. 运行分析Agent
                logger.info("🔄 正在询问分析Agent...")
                analysis_result = self.analysis_agent.run(user_input)

                if analysis_result.get("need_planning", True):
                    # 2. 运行规划Agent
                    logger.info("🔄 正在询问规划Agent...")
                    planning_result = self.planning_agent.run(user_input)
                    MemoryManager.save_json("planning_result.json", planning_result)

                    # 3. 新增：调用细化Agent
                    logger.info("🔄 正在调用细化Agent...")
                    refinement_result = self.refinement_agent.run()

                    return {
                        "status": "success",
                        "message": "完成需求分析、任务规划和步骤细化",
                        "analysis_result": analysis_result,
                        "planning_result": planning_result,
                        "refinement_result": refinement_result,  # 新增细化结果
                    }

                else:
                    # 普通回复流程（保持循环）
                    logger.info("🔄 正在询问普通回复Agent...")
                    ordinary_reply = self.ordinary_reply_agent.run(user_input)

                    if reply_content := ordinary_reply.get("reply"):
                        print(f"Assistant: {reply_content}")

                    # 获取新输入并检查退出命令
                    user_input = input("\n用户：")
                    continue  # 继续下一次循环

            except Exception as e:
                logger.error(f"工作流程执行失败: {e}")
                return {
                    "status": "error",
                    "message": f"工作流程执行失败: {str(e)}",
                    "result": None,
                }


# 创建全局Workflow实例
_workflow_instance = None


def get_workflow_instance() -> Workflow:
    """获取Workflow实例

    Returns:
        Workflow实例
    """
    global _workflow_instance

    if _workflow_instance is None:
        _workflow_instance = Workflow()

    return _workflow_instance


def run_workflow(user_input: str) -> Dict[str, Any]:
    """运行工作流程

    Args:
        user_input: 用户输入

    Returns:
        执行结果字典
    """
    workflow = get_workflow_instance()
    return workflow.execute(user_input)
