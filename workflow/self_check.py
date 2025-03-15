#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
workflow/self_check.py - 工作流自检查模块

该模块负责系统启动时的自检查流程，确保各组件正常运行。
"""

import os
import sys
import importlib
import logging
from typing import Dict, List, Any, Tuple

def check_environment() -> Dict[str, Any]:
    """
    检查系统环境
    
    Returns:
        Dict[str, Any]: 环境检查结果
    """
    result = {
        'status': 'success',
        'python_version': sys.version,
        'checks': []
    }
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        result['checks'].append({
            'name': 'python_version',
            'status': 'error',
            'message': f'Python版本需要 >= 3.8，当前版本: {python_version.major}.{python_version.minor}.{python_version.micro}'
        })
    else:
        result['checks'].append({
            'name': 'python_version',
            'status': 'success',
            'message': f'Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}'
        })
    
    # 检查必要的系统模块
    required_modules = ['json', 'logging', 'datetime', 'os', 'sys']
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
            result['checks'].append({
                'name': f'module_{module_name}',
                'status': 'success',
                'message': f'系统模块 {module_name} 已安装'
            })
        except ImportError:
            result['checks'].append({
                'name': f'module_{module_name}',
                'status': 'error',
                'message': f'系统模块 {module_name} 未安装'
            })
            result['status'] = 'error'
    
    return result

def check_agents() -> Dict[str, Any]:
    """
    检查系统中的所有Agent
    
    Returns:
        Dict[str, Any]: Agent检查结果
    """
    result = {
        'status': 'success',
        'checks': []
    }
    
    # 检查必要的Agent模块
    required_agents = [
        ('agent.step_agent', 'StepAgent'),
        ('agent.analysis_agent', 'AnalysisAgent'),
        ('agent.execution_agent', 'ExecutionAgent'),
        ('agent.review_agent', 'ReviewAgent'),
        ('agent.fix_agent', 'FixAgent'),
        ('agent.summary_agent', 'SummaryAgent')
    ]
    
    for module_path, class_name in required_agents:
        try:
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            result['checks'].append({
                'name': f'agent_{class_name}',
                'status': 'success',
                'message': f'Agent {class_name} 已加载'
            })
        except (ImportError, AttributeError) as e:
            result['checks'].append({
                'name': f'agent_{class_name}',
                'status': 'error',
                'message': f'Agent {class_name} 加载失败: {str(e)}'
            })
            result['status'] = 'error'
    
    return result

def check_tools() -> Dict[str, Any]:
    """
    检查系统中的所有工具
    
    Returns:
        Dict[str, Any]: 工具检查结果
    """
    result = {
        'status': 'success',
        'checks': []
    }
    
    # 检查工具目录是否存在
    tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools')
    if not os.path.exists(tools_dir) or not os.path.isdir(tools_dir):
        result['status'] = 'error'
        result['checks'].append({
            'name': 'tools_directory',
            'status': 'error',
            'message': f'工具目录不存在: {tools_dir}'
        })
        return result
    
    result['checks'].append({
        'name': 'tools_directory',
        'status': 'success',
        'message': f'工具目录存在: {tools_dir}'
    })
    
    # 检查工具模块
    tool_modules = [
        ('tools.text_analyzer.analyzer', ['extract_keywords', 'analyze_sentiment', 'count_statistics'])
    ]
    
    for module_path, functions in tool_modules:
        try:
            module = importlib.import_module(module_path)
            for function_name in functions:
                if hasattr(module, function_name):
                    result['checks'].append({
                        'name': f'tool_{module_path}.{function_name}',
                        'status': 'success',
                        'message': f'工具函数 {function_name} 已加载'
                    })
                else:
                    result['checks'].append({
                        'name': f'tool_{module_path}.{function_name}',
                        'status': 'error',
                        'message': f'工具函数 {function_name} 不存在'
                    })
                    result['status'] = 'error'
        except ImportError as e:
            result['checks'].append({
                'name': f'tool_{module_path}',
                'status': 'error',
                'message': f'工具模块 {module_path} 加载失败: {str(e)}'
            })
            result['status'] = 'error'
    
    return result

def check_memory() -> Dict[str, Any]:
    """
    检查记忆系统
    
    Returns:
        Dict[str, Any]: 记忆系统检查结果
    """
    result = {
        'status': 'success',
        'checks': []
    }
    
    try:
        from memory.conversation import ConversationMemory
        memory = ConversationMemory()
        
        # 测试记忆功能
        test_message = "测试消息"
        memory.add_user_message(test_message)
        history = memory.get_conversation_history()
        
        if test_message in str(history):
            result['checks'].append({
                'name': 'memory_conversation',
                'status': 'success',
                'message': '对话记忆系统工作正常'
            })
        else:
            result['checks'].append({
                'name': 'memory_conversation',
                'status': 'error',
                'message': '对话记忆系统工作异常'
            })
            result['status'] = 'error'
    except Exception as e:
        result['checks'].append({
            'name': 'memory_conversation',
            'status': 'error',
            'message': f'对话记忆系统检查失败: {str(e)}'
        })
        result['status'] = 'error'
    
    return result

def run_self_check(logger: logging.Logger = None) -> Dict[str, Any]:
    """
    运行完整的自检查流程
    
    Args:
        logger: 日志记录器，如果为None则创建新的记录器
        
    Returns:
        Dict[str, Any]: 自检查结果
    """
    if logger is None:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger = logging.getLogger('self_check')
    
    logger.info("开始系统自检查")
    
    result = {
        'status': 'success',
        'timestamp': str(import_datetime().now()),
        'checks': {}
    }
    
    # 检查环境
    logger.info("检查系统环境")
    env_result = check_environment()
    result['checks']['environment'] = env_result
    if env_result['status'] == 'error':
        result['status'] = 'error'
    
    # 检查Agent
    logger.info("检查Agent组件")
    agents_result = check_agents()
    result['checks']['agents'] = agents_result
    if agents_result['status'] == 'error':
        result['status'] = 'error'
    
    # 检查工具
    logger.info("检查工具组件")
    tools_result = check_tools()
    result['checks']['tools'] = tools_result
    if tools_result['status'] == 'error':
        result['status'] = 'error'
    
    # 检查记忆系统
    logger.info("检查记忆系统")
    memory_result = check_memory()
    result['checks']['memory'] = memory_result
    if memory_result['status'] == 'error':
        result['status'] = 'error'
    
    logger.info(f"系统自检查完成，状态: {result['status']}")
    return result

def import_datetime():
    """
    导入datetime模块
    
    Returns:
        module: datetime模块
    """
    import datetime
    return datetime

if __name__ == "__main__":
    # 直接运行此脚本时执行自检查
    import json
    result = run_self_check()
    print(json.dumps(result, indent=2, ensure_ascii=False))