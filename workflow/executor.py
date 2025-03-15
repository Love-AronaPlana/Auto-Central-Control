#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
workflow/executor.py - 工作流执行器模块

该模块负责执行具体的工作流程，包括调用各个Agent执行任务、处理中间结果等。
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime


class WorkflowExecutor:
    """
    工作流执行器类，负责执行具体的工作流程
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger | None = None):
        """
        初始化工作流执行器

        Args:
            config: 系统配置信息
            logger: 日志记录器
        """
        self.config = config

        if logger is None:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            self.logger = logging.getLogger("workflow_executor")
        else:
            self.logger = logger

        # 初始化Agent和记忆系统
        self._init_components()

    def _init_components(self):
        """
        初始化工作流所需的组件
        """
        try:
            # 导入必要的模块
            from agent.step_agent import StepAgent
            from agent.analysis_agent import AnalysisAgent
            from agent.execution_agent import ExecutionAgent
            from agent.review_agent import ReviewAgent
            from agent.fix_agent import FixAgent
            from agent.summary_agent import SummaryAgent
            from memory.conversation import ConversationMemory

            # 初始化Agent
            self.step_agent = StepAgent(self.config)
            self.analysis_agent = AnalysisAgent(self.config)
            self.execution_agent = ExecutionAgent(self.config)
            self.review_agent = ReviewAgent(self.config)
            self.fix_agent = FixAgent(self.config)
            self.summary_agent = SummaryAgent(self.config)

            # 初始化对话记忆
            self.memory = ConversationMemory()

            self.logger.info("工作流组件初始化完成")
        except Exception as e:
            self.logger.error(f"工作流组件初始化失败: {str(e)}", exc_info=True)
            raise

    def execute(self, user_input: str) -> Dict[str, Any]:
        """
        执行工作流程

        Args:
            user_input: 用户输入的需求

        Returns:
            Dict[str, Any]: 执行结果
        """
        self.logger.info("开始执行工作流程")
        result = {
            "status": "success",
            "timestamp": str(datetime.now()),
            "steps_completed": 0,
            "steps_total": 0,
            "summary": "",
        }

        try:
            # 记录用户输入
            self.memory.add_user_message(user_input)

            # 步骤1: 使用步骤Agent将用户需求分解为详细步骤
            self.logger.info("步骤1: 分解用户需求为详细步骤")
            steps = self.step_agent.process(user_input)
            self.memory.add_system_message("步骤Agent已将用户需求分解为以下步骤：")
            self.memory.add_system_message(
                json.dumps(steps, ensure_ascii=False, indent=2)
            )

            result["steps_total"] = len(steps)

            # 循环执行每个步骤
            current_step_index = 0
            total_steps = len(steps)

            while current_step_index < total_steps:
                current_step = steps[current_step_index]
                self.logger.info(
                    f"开始执行步骤 {current_step_index + 1}/{total_steps}: {current_step['description']}"
                )

                # 步骤2: 使用分析Agent确定如何执行当前步骤
                self.logger.info("步骤2: 分析如何执行当前步骤")
                execution_plan = self.analysis_agent.process(
                    current_step, self.memory.get_conversation_history()
                )
                self.memory.add_system_message("分析Agent已确定执行计划：")
                self.memory.add_system_message(
                    json.dumps(execution_plan, ensure_ascii=False, indent=2)
                )

                # 步骤3: 使用执行Agent执行当前步骤
                self.logger.info("步骤3: 执行当前步骤")
                execution_result = self.execution_agent.process(
                    execution_plan, self.memory.get_conversation_history()
                )
                self.memory.add_system_message("执行Agent已完成步骤执行：")
                self.memory.add_system_message(
                    json.dumps(execution_result, ensure_ascii=False, indent=2)
                )

                # 步骤4: 使用复查Agent检查执行结果
                self.logger.info("步骤4: 复查执行结果")
                review_result = self.review_agent.process(
                    execution_result,
                    current_step,
                    self.memory.get_conversation_history(),
                )
                self.memory.add_system_message("复查Agent已检查执行结果：")
                self.memory.add_system_message(
                    json.dumps(review_result, ensure_ascii=False, indent=2)
                )

                # 如果复查发现错误，使用修复Agent进行修复
                if review_result.get("has_errors", False):
                    self.logger.info("发现错误，开始修复")
                    fix_attempts = 0
                    max_fix_attempts = 3  # 最大修复尝试次数

                    while (
                        review_result.get("has_errors", False)
                        and fix_attempts < max_fix_attempts
                    ):
                        fix_attempts += 1
                        self.logger.info(f"修复尝试 {fix_attempts}/{max_fix_attempts}")

                        # 步骤5: 使用修复Agent修复错误
                        fix_result = self.fix_agent.process(
                            review_result, self.memory.get_conversation_history()
                        )
                        self.memory.add_system_message(
                            f"修复Agent已尝试修复错误（第{fix_attempts}次）："
                        )
                        self.memory.add_system_message(
                            json.dumps(fix_result, ensure_ascii=False, indent=2)
                        )

                        # 再次复查
                        review_result = self.review_agent.process(
                            fix_result,
                            current_step,
                            self.memory.get_conversation_history(),
                        )
                        self.memory.add_system_message(
                            f"复查Agent已再次检查执行结果（第{fix_attempts}次）："
                        )
                        self.memory.add_system_message(
                            json.dumps(review_result, ensure_ascii=False, indent=2)
                        )

                    if review_result.get("has_errors", False):
                        self.logger.warning(
                            f"在{max_fix_attempts}次尝试后仍无法修复所有错误，继续执行下一步骤"
                        )

                # 移动到下一个步骤
                current_step_index += 1
                result["steps_completed"] = current_step_index

            # 所有步骤执行完毕，使用结束Agent进行总结
            self.logger.info("所有步骤执行完毕，开始总结")
            summary_result = self.summary_agent.process(
                steps, self.memory.get_conversation_history()
            )
            self.memory.add_system_message("结束Agent已总结执行结果：")
            self.memory.add_system_message(
                json.dumps(summary_result, ensure_ascii=False, indent=2)
            )

            result["summary"] = summary_result.get("summary", "执行完成，但未生成总结")
            self.logger.info("工作流程执行完成")

        except Exception as e:
            self.logger.error(f"工作流程执行出错: {str(e)}", exc_info=True)
            result["status"] = "error"
            result["error"] = str(e)

        return result


# 工作流执行函数，用于从外部调用
def execute_workflow(
    config: Dict[str, Any], user_input: str, logger: logging.Logger | None = None
) -> Dict[str, Any]:
    """
    执行工作流程的便捷函数

    Args:
        config: 系统配置信息
        user_input: 用户输入的需求
        logger: 日志记录器

    Returns:
        Dict[str, Any]: 执行结果
    """
    executor = WorkflowExecutor(config, logger)
    return executor.execute(user_input)


if __name__ == "__main__":
    # 直接运行此脚本时的测试代码
    if len(sys.argv) > 1:
        test_input = " ".join(sys.argv[1:])
    else:
        test_input = input("请输入测试需求: ")

    # 简单的测试配置
    test_config = {"model": "gpt-3.5-turbo", "temperature": 0.7, "max_tokens": 1000}

    result = execute_workflow(test_config, test_input)
    print(json.dumps(result, indent=2, ensure_ascii=False))
