#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
workflow/main.py - 工作流主模块

该模块负责协调整个系统的工作流程，按照预定义的步骤执行各个Agent。
"""

import os
import sys
import json
import logging
from datetime import datetime

# 工作流程序主入口
def start_workflow(config, logger):
    """
    启动工作流程
    
    Args:
        config: 系统配置信息
        logger: 日志记录器
    """
    logger.info("开始执行工作流程")
    
    try:
        # 导入必要的模块
        from agent.step_agent import StepAgent
        from agent.analysis_agent import AnalysisAgent
        from agent.execution_agent import ExecutionAgent
        from agent.review_agent import ReviewAgent
        from agent.fix_agent import FixAgent
        from agent.summary_agent import SummaryAgent
        from memory.conversation import ConversationMemory
        
        # 初始化对话记忆
        memory = ConversationMemory()
        
        # 获取用户输入
        user_input = get_user_input()
        memory.add_user_message(user_input)
        
        # 步骤1: 使用步骤Agent将用户需求分解为详细步骤
        logger.info("步骤1: 分解用户需求为详细步骤")
        step_agent = StepAgent(config)
        steps = step_agent.process(user_input)
        memory.add_system_message("步骤Agent已将用户需求分解为以下步骤：")
        memory.add_system_message(json.dumps(steps, ensure_ascii=False, indent=2))
        
        # 循环执行每个步骤
        current_step_index = 0
        total_steps = len(steps)
        
        while current_step_index < total_steps:
            current_step = steps[current_step_index]
            logger.info(f"开始执行步骤 {current_step_index + 1}/{total_steps}: {current_step['description']}")
            
            # 步骤2: 使用分析Agent确定如何执行当前步骤
            logger.info("步骤2: 分析如何执行当前步骤")
            analysis_agent = AnalysisAgent(config)
            execution_plan = analysis_agent.process(current_step, memory.get_conversation_history())
            memory.add_system_message("分析Agent已确定执行计划：")
            memory.add_system_message(json.dumps(execution_plan, ensure_ascii=False, indent=2))
            
            # 步骤3: 使用执行Agent执行当前步骤
            logger.info("步骤3: 执行当前步骤")
            execution_agent = ExecutionAgent(config)
            execution_result = execution_agent.process(execution_plan, memory.get_conversation_history())
            memory.add_system_message("执行Agent已完成步骤执行：")
            memory.add_system_message(json.dumps(execution_result, ensure_ascii=False, indent=2))
            
            # 步骤4: 使用复查Agent检查执行结果
            logger.info("步骤4: 复查执行结果")
            review_agent = ReviewAgent(config)
            review_result = review_agent.process(execution_result, current_step, memory.get_conversation_history())
            memory.add_system_message("复查Agent已检查执行结果：")
            memory.add_system_message(json.dumps(review_result, ensure_ascii=False, indent=2))
            
            # 如果复查发现错误，使用修复Agent进行修复
            if review_result.get('has_errors', False):
                logger.info("发现错误，开始修复")
                fix_attempts = 0
                max_fix_attempts = 3  # 最大修复尝试次数
                
                while review_result.get('has_errors', False) and fix_attempts < max_fix_attempts:
                    fix_attempts += 1
                    logger.info(f"修复尝试 {fix_attempts}/{max_fix_attempts}")
                    
                    # 步骤5: 使用修复Agent修复错误
                    fix_agent = FixAgent(config)
                    fix_result = fix_agent.process(review_result, memory.get_conversation_history())
                    memory.add_system_message(f"修复Agent已尝试修复错误（第{fix_attempts}次）：")
                    memory.add_system_message(json.dumps(fix_result, ensure_ascii=False, indent=2))
                    
                    # 再次复查
                    review_result = review_agent.process(fix_result, current_step, memory.get_conversation_history())
                    memory.add_system_message(f"复查Agent已再次检查执行结果（第{fix_attempts}次）：")
                    memory.add_system_message(json.dumps(review_result, ensure_ascii=False, indent=2))
                
                if review_result.get('has_errors', False):
                    logger.warning(f"在{max_fix_attempts}次尝试后仍无法修复所有错误，继续执行下一步骤")
            
            # 移动到下一个步骤
            current_step_index += 1
        
        # 所有步骤执行完毕，使用结束Agent进行总结
        logger.info("所有步骤执行完毕，开始总结")
        summary_agent = SummaryAgent(config)
        summary = summary_agent.process(steps, memory.get_conversation_history())
        memory.add_system_message("结束Agent已总结执行结果：")
        memory.add_system_message(json.dumps(summary, ensure_ascii=False, indent=2))
        
        # 输出总结给用户
        print("\n" + "=" * 50)
        print("执行完成！以下是执行总结：")
        print(summary['summary'])
        print("=" * 50 + "\n")
        
        logger.info("工作流程执行完成")
        return True
        
    except Exception as e:
        logger.error(f"工作流程执行出错: {str(e)}", exc_info=True)
        print(f"执行出错: {str(e)}")
        return False

# 获取用户输入
def get_user_input():
    """
    获取用户输入的需求
    
    Returns:
        str: 用户输入的需求文本
    """
    print("\n" + "=" * 50)
    print("欢迎使用Auto-Central-Control系统！")
    print("请输入您需要执行的任务：")
    print("=" * 50)
    
    user_input = input("> ")
    return user_input