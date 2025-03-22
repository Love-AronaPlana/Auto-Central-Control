"""ACC工作流程控制模块

该模块负责控制ACC系统的主要工作流程，包括：
- 初始化系统组件
- 协调各个Agent的工作
- 处理执行结果
- 管理系统状态
"""

import json
import logging
import os
import re
from typing import Dict, Any

from ACC.agent.planning import PlanningAgent
from ACC.agent.analysis import AnalysisAgent

# 修改导入，添加MEMORY_DIR
from ACC.memory.memory_manager import MemoryManager, MEMORY_DIR

logger = logging.getLogger(__name__)


# 在顶部添加导入
from ACC.agent.refinement import RefinementAgent

# 添加操作Agent导入
from ACC.agent.operate import OperateAgent


from ACC.config import get_default_workspace_path


# 在文件顶部添加导入
from ACC.agent.sumup import SumupAgent

class Workflow:
    """ACC工作流程控制类"""

    def __init__(self):
        """初始化工作流程控制器"""
        logger.info("初始化工作流程控制器")

        # 清空历史记录（新增）
        MemoryManager.clean_history_file()

        # 原有清空目录操作
        MemoryManager.clean_todo_directory()
        MemoryManager.clean_refinement_directory()
        # 添加清空操作目录
        MemoryManager.clean_operation_directory()
        # 添加清空操作解释目录
        MemoryManager.clean_operation_generalization_directory()

        # 初始化Agent（原有代码）
        self.analysis_agent = AnalysisAgent()
        self.planning_agent = PlanningAgent()
        self.refinement_agent = RefinementAgent()
        # 添加操作Agent
        self.operate_agent = OperateAgent()

        # 确保目录存在（原有代码）
        self._ensure_directories()

    # 在文件顶部导入
    from ACC.config import get_default_workspace_path

    # 在_ensure_directories方法中添加工作空间目录的创建
    def _ensure_directories(self):
        """确保必要的目录存在"""
        # 确保操作目录存在
        operation_dir = os.path.join(MEMORY_DIR, "todo", "operation")
        if not os.path.exists(operation_dir):
            os.makedirs(operation_dir, exist_ok=True)
            logger.info(f"创建目录: {operation_dir}")

        # 确保历史记录目录存在
        operation_gen_dir = os.path.join(MEMORY_DIR, "operation_generalization")
        if not os.path.exists(operation_gen_dir):
            os.makedirs(operation_gen_dir, exist_ok=True)
            logger.info(f"创建目录: {operation_gen_dir}")

            # 确保工作空间目录存在
            workspace_dir = get_default_workspace_path()
            workspace_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                workspace_dir,
            )
            if not os.path.exists(workspace_path):
                os.makedirs(workspace_path, exist_ok=True)
                logger.info(f"创建工作空间目录: {workspace_path}")

    # 修改 execute 方法中的循环处理逻辑
    def execute(self, user_input: str) -> Dict[str, Any]:
        """执行工作流程"""
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
    
                # 添加总结Agent
                self.sumup_agent = SumupAgent()
    
                # 循环处理所有未完成的任务
                all_tasks_completed = False
                operation_results = []
    
                while not all_tasks_completed:
                    # 3. 运行细化Agent - 只执行一次
                    logger.info("🔄 正在询问细化Agent...")
                    refinement_result = self.refinement_agent.run()
    
                    # 获取当前处理的任务编号
                    current_task = refinement_result.get("current_task", "")
                    task_number_match = re.search(r"^(\d+\.\d+)", current_task)
    
                    if not task_number_match:
                        logger.error(f"无法识别任务编号: {current_task}")
                        return {
                            "status": "error",
                            "message": f"无法识别任务编号: {current_task}",
                        }
    
                    task_number = task_number_match.group()
                    refinement_file = (
                        f"todo/refinement/{task_number.replace('.', '_')}.md"
                    )
    
                    # 确保细化文件存在
                    if not os.path.exists(os.path.join(MEMORY_DIR, refinement_file)):
                        logger.error(f"细化文件不存在: {refinement_file}")
                        return {
                            "status": "error",
                            "message": f"细化文件不存在: {refinement_file}",
                        }
    
                    # 4. 循环调用操作Agent直到当前任务完成
                    current_task_completed = False
                    while not current_task_completed:
                        logger.info(f"🔄 正在调用操作Agent处理任务 {task_number}...")
                        operation_result = self.operate_agent.run(refinement_file)
                        operation_results.append(operation_result)
    
                        # 处理操作结果
                        if "error" in operation_result and not operation_result.get("success", False):
                            logger.error(f"操作Agent执行失败: {operation_result['error']}，但将继续尝试")
                            # 不返回错误，继续尝试执行
    
                        # 检查操作是否成功完成
                        operation_success = operation_result.get("success", False)
    
                        # 如果操作未成功完成，不清空历史记录，并将工具返回内容添加到历史对话
                        if not operation_success:
                            logger.info("操作未成功完成，保留历史记录")
    
                            # 如果有工具执行结果，将其添加到历史对话
                            if tool_result := operation_result.get("tool_result"):
                                logger.info(f"添加工具执行结果到历史对话: {tool_result}")
    
                                # 读取当前历史记录
                                history = MemoryManager.read_json("history.json")
    
                                # 添加工具执行结果到历史记录
                                history.append(
                                    {
                                        "role": "tool_result",
                                        "content": json.dumps(
                                            tool_result, ensure_ascii=False
                                        ),
                                    }
                                )
    
                                # 保存更新后的历史记录
                                MemoryManager.save_json("history.json", history)
    
                            # 添加explanation到历史对话
                            if explanation := operation_result.get("explanation"):
                                logger.info(
                                    f"添加操作解释到历史对话: {explanation[:100]}..."
                                )
    
                                # 读取当前历史记录
                                history = MemoryManager.read_json("history.json")
    
                                # 添加explanation到历史记录，角色为assistant
                                history.append(
                                    {"role": "assistant", "content": explanation}
                                )
    
                                # 保存更新后的历史记录
                                MemoryManager.save_json("history.json", history)
                        else:
                            # 操作成功，更新planning.md中的任务状态
                            self._update_planning_task_status(task_number)
                            current_task_completed = True
                            logger.info(f"任务 {task_number} 已完成")
    
                    # 检查是否还有未完成的任务
                    all_tasks_completed = self._check_all_tasks_completed()
    
                # 所有任务完成后，运行总结Agent
                logger.info("🔄 正在生成系统执行总结报告...")
                summary_result = self.sumup_agent.run()
                
                return {
                    "status": "success",
                    "message": "所有任务已完成",
                    "operation_results": operation_results,
                    "summary": summary_result.get("summary")
                }
            else:
                # 直接返回分析结果
                return {
                    "status": "success",
                    "message": "完成需求分析",
                    "analysis_result": analysis_result,
                }
    
        except Exception as e:
            logger.error(f"工作流程执行异常: {e}")
            return {"status": "error", "message": f"执行异常: {e}"}

    def _update_planning_task_status(self, task_number: str) -> bool:
        """更新planning.md中的任务状态为已完成

        Args:
            task_number: 任务编号，如"1.1"

        Returns:
            更新是否成功
        """
        try:
            planning_path = os.path.join(MEMORY_DIR, "todo", "planning.md")

            # 读取planning.md内容
            with open(planning_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 替换对应任务的状态
            pattern = r"- \[ \] " + re.escape(task_number)
            replacement = f"- [x] {task_number}"
            updated_content = re.sub(pattern, replacement, content)

            # 写回文件
            with open(planning_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            logger.info(f"已将任务 {task_number} 标记为已完成")
            return True
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            return False

    def _check_all_tasks_completed(self) -> bool:
        """检查planning.md中是否所有任务都已完成

        Returns:
            是否所有任务都已完成
        """
        try:
            planning_path = os.path.join(MEMORY_DIR, "todo", "planning.md")

            # 读取planning.md内容
            with open(planning_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 查找是否还有未完成的任务
            if re.search(r"- \[ \]", content):
                return False
            return True
        except Exception as e:
            logger.error(f"检查任务完成状态失败: {e}")
            return True  # 出错时默认认为所有任务已完成，避免无限循环


# 单例模式
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
        执行结果
    """
    workflow = get_workflow_instance()
    return workflow.execute(user_input)
