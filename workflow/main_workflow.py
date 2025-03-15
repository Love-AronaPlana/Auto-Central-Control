#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工作流主模块 - 负责协调各个Agent的工作流程
"""

import os
import sys
import json
import logging
from datetime import datetime
import importlib

# 导入各个Agent模块
from agent.step_agent import StepAgent
from agent.analyze_agent import AnalyzeAgent
from agent.execute_agent import ExecuteAgent
from agent.review_agent import ReviewAgent
from agent.fix_agent import FixAgent
from agent.finish_agent import FinishAgent

# 导入内存管理模块
from memory.memory_manager import MemoryManager

def start_workflow():
    """
    启动工作流程
    """
    logging.info("启动工作流程")
    
    # 初始化内存管理器
    memory_manager = MemoryManager()
    
    try:
        # 获取用户输入
        user_input = get_user_input()
        logging.info(f"用户输入: {user_input}")
        
        # 保存用户输入到内存
        memory_manager.save('user_input', user_input)
        
        # 步骤1: 使用步骤Agent分解任务
        step_agent = StepAgent()
        steps = step_agent.process(user_input)
        logging.info(f"任务分解为 {len(steps)} 个步骤")
        
        # 保存步骤到内存
        memory_manager.save('steps', steps)
        
        # 初始化步骤状态
        current_step_index = 0
        steps_status = [{'status': 'pending', 'result': None} for _ in steps]
        memory_manager.save('steps_status', steps_status)
        
        # 循环执行每个步骤
        while current_step_index < len(steps):
            current_step = steps[current_step_index]
            logging.info(f"开始执行步骤 {current_step_index + 1}: {current_step['description']}")
            
            # 步骤2: 使用分析Agent判断如何执行当前步骤
            analyze_agent = AnalyzeAgent()
            execution_plan = analyze_agent.process(current_step, user_input)
            logging.info(f"分析结果: {execution_plan['summary']}")
            
            # 保存执行计划到内存
            memory_manager.save(f'execution_plan_{current_step_index}', execution_plan)
            
            # 步骤3: 使用执行Agent执行操作
            execute_agent = ExecuteAgent()
            execution_result = execute_agent.process(execution_plan)
            logging.info(f"执行结果: {execution_result['status']}")
            
            # 保存执行结果到内存
            memory_manager.save(f'execution_result_{current_step_index}', execution_result)
            
            # 步骤4: 使用复查Agent检查执行结果
            review_agent = ReviewAgent()
            review_result = review_agent.process(execution_result, current_step)
            logging.info(f"复查结果: {review_result['status']}")
            
            # 如果复查发现错误，使用修复Agent修复
            if review_result['status'] == 'error':
                logging.warning(f"发现错误: {review_result['error_message']}")
                
                # 循环修复直到没有错误
                fix_attempts = 0
                max_fix_attempts = 3  # 最大修复尝试次数
                
                while review_result['status'] == 'error' and fix_attempts < max_fix_attempts:
                    # 步骤5: 使用修复Agent修复错误
                    fix_agent = FixAgent()
                    fix_result = fix_agent.process(review_result, execution_result, current_step)
                    logging.info(f"修复结果: {fix_result['status']}")
                    
                    # 保存修复结果到内存
                    memory_manager.save(f'fix_result_{current_step_index}_{fix_attempts}', fix_result)
                    
                    # 重新执行复查
                    review_result = review_agent.process(fix_result, current_step)
                    logging.info(f"复查修复结果: {review_result['status']}")
                    
                    fix_attempts += 1
                
                if review_result['status'] == 'error':
                    logging.error(f"步骤 {current_step_index + 1} 修复失败，达到最大尝试次数")
                    # 更新步骤状态
                    steps_status[current_step_index] = {'status': 'failed', 'result': review_result}
                    memory_manager.save('steps_status', steps_status)
                    break
            
            # 更新步骤状态
            steps_status[current_step_index] = {'status': 'completed', 'result': review_result}
            memory_manager.save('steps_status', steps_status)
            
            # 进入下一个步骤
            current_step_index += 1
        
        # 步骤6: 使用结束Agent总结执行结果
        finish_agent = FinishAgent()
        summary = finish_agent.process(steps, steps_status, user_input)
        logging.info(f"执行总结: {summary['summary']}")
        
        # 输出总结结果
        print("\n" + "=" * 50)
        print("执行完成！")
        print(summary['summary'])
        print("=" * 50 + "\n")
        
        return True
        
    except Exception as e:
        logging.error(f"工作流执行出错: {str(e)}", exc_info=True)
        print(f"\n错误: {str(e)}\n")
        return False

def get_user_input():
    """
    获取用户输入
    """
    print("\n" + "=" * 50)
    print("欢迎使用Auto-Central-Control系统")
    print("请输入您需要执行的操作:")
    print("=" * 50 + "\n")
    
    user_input = input("> ")
    return user_input

if __name__ == "__main__":
    # 直接运行此模块进行测试
    start_workflow()