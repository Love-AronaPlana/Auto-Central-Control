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

logger = logging.getLogger(__name__)


# 在顶部添加导入
from ASN.agent.refinement import RefinementAgent


class Workflow:
    """ASN工作流程控制类"""

    def __init__(self):
        """初始化工作流程控制器"""
        logger.info("初始化工作流程控制器")

        # 清空历史记录（新增）
        MemoryManager.clean_history_file()

        # 原有清空目录操作
        MemoryManager.clean_todo_directory()
        MemoryManager.clean_refinement_directory()

        # 初始化Agent（原有代码）
        self.analysis_agent = AnalysisAgent()
        self.planning_agent = PlanningAgent()
        self.refinement_agent = RefinementAgent()

        # 确保目录存在（原有代码）
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

                    # 3. 调用细化Agent
                    logger.info("🔄 正在调用细化Agent...")
                    refinement_result = self.refinement_agent.run()

                    return {
                        "status": "success",
                        "message": "完成需求分析、任务规划和步骤细化",
                        "analysis_result": analysis_result,
                        "planning_result": planning_result,
                        "refinement_result": refinement_result,
                    }

                # 不需要规划时直接进入新输入循环
                print(
                    f"\nAssistant: {analysis_result.get('message', '已收到您的请求')}"
                )

            except Exception as e:  # 确保此except与try对齐
                logger.error(f"工作流程执行异常: {str(e)}")
                print(f"\n系统错误: {str(e)}")

            # 获取新输入（移到try-except块外）
            print("\n请输入您的需求（按下两次回车键提交，输入'exit/退出'退出程序）:")
            user_input = ""
            while True:
                line = input()
                if line.lower() in ("exit", "退出"):
                    return {"status": "exit", "message": "用户请求退出系统"}
                if line == "":
                    if len(user_input.splitlines()) >= 1:
                        break
                user_input += line + "\n"

        # 删除以下多余的except块
        # except Exception as e:  # 确保这个 except 与上层的 try 对齐
        #    logger.error(f"工作流程执行失败: {e}")
        #    return {
        #        "status": "error",
        #        "message": f"工作流程执行失败: {str(e)}",
        #        "result": None,
        #    }


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
