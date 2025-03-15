#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
执行Agent模块 - 负责使用可用工具执行具体操作
"""

import os
import json
import logging
import importlib
import openai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class ExecuteAgent:
    """
    执行Agent类 - 使用可用工具执行具体操作
    """
    
    def __init__(self):
        """
        初始化执行Agent
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_base = os.getenv('OPENAI_API_BASE')
        self.model = os.getenv('OPENAI_MODEL')
        
        # 设置OpenAI API
        openai.api_key = self.api_key
        if self.api_base and self.api_base != 'https://api.openai.com/v1':
            openai.api_base = self.api_base
        
        # 加载提示词
        self.system_prompt = self._load_prompt('execute_agent_prompt.txt')
        
        # 加载可用工具
        self.available_tools = self._load_tools()
    
    def _load_prompt(self, prompt_file):
        """
        加载提示词文件
        
        Args:
            prompt_file (str): 提示词文件名
            
        Returns:
            str: 提示词内容
        """
        prompt_path = os.path.join('agent', 'prompts', prompt_file)
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logging.error(f"加载提示词文件失败: {prompt_file}, 错误: {str(e)}")
            # 返回默认提示词
            return """你是一个执行专家。你的任务是使用可用工具执行给定的操作计划。
请根据执行计划选择合适的工具，并按照正确的顺序执行操作。
如果需要使用工具，请以JSON格式返回工具名称和参数。
执行完成后，请以JSON格式返回执行结果和状态。"""
    
    def _load_tools(self):
        """
        加载可用工具
        
        Returns:
            dict: 工具名称和工具模块的映射
        """
        tools = {}
        tools_dir = os.path.join('plugins', 'tools')
        
        if not os.path.exists(tools_dir):
            logging.warning(f"工具目录不存在: {tools_dir}")
            return tools
        
        # 遍历工具目录
        for file in os.listdir(tools_dir):
            if file.endswith('.py') and not file.startswith('__'):
                tool_name = file[:-3]  # 去掉.py后缀
                try:
                    # 动态导入工具模块
                    module_path = f"plugins.tools.{tool_name}"
                    tool_module = importlib.import_module(module_path)
                    
                    # 检查模块是否有execute函数
                    if hasattr(tool_module, 'execute'):
                        tools[tool_name] = tool_module
                        logging.info(f"成功加载工具: {tool_name}")
                    else:
                        logging.warning(f"工具模块缺少execute函数: {tool_name}")
                except Exception as e:
                    logging.error(f"加载工具失败: {tool_name}, 错误: {str(e)}")
        
        return tools
    
    def process(self, execution_plan):
        """
        处理执行计划，执行具体操作
        
        Args:
            execution_plan (dict): 执行计划，包含执行方法、所需工具和预期结果
            
        Returns:
            dict: 执行结果，包含状态、输出和错误信息
        """
        logging.info(f"执行Agent开始处理执行计划")
        
        # 初始化执行结果
        execution_result = {
            'status': 'pending',
            'output': None,
            'error': None,
            'step': execution_plan['step'],
            'tools_used': []
        }
        
        try:
            # 构建提示词
            tools_info = "\n".join([f"- {name}: {module.__doc__ or '无描述'}" for name, module in self.available_tools.items()])
            prompt = f"执行计划:\n{json.dumps(execution_plan, ensure_ascii=False, indent=2)}\n\n可用工具:\n{tools_info}"
            
            # 执行对话，直到完成或达到最大对话轮数
            max_turns = 10
            current_turn = 0
            conversation_history = []
            
            while current_turn < max_turns and execution_result['status'] == 'pending':
                # 调用OpenAI API
                messages = [
                    {"role": "system", "content": self.system_prompt}
                ]
                
                # 添加对话历史
                for msg in conversation_history:
                    messages.append(msg)
                
                # 添加当前提示词（仅在第一轮对话时）
                if current_turn == 0:
                    messages.append({"role": "user", "content": prompt})
                
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                )
                
                # 解析响应
                content = response.choices[0].message.content
                conversation_history.append({"role": "assistant", "content": content})
                logging.debug(f"执行Agent响应 (轮次 {current_turn + 1}): {content}")
                
                # 尝试解析JSON
                try:
                    action = json.loads(content)
                    
                    # 检查是否完成执行
                    if 'status' in action and action['status'] in ['completed', 'failed']:
                        execution_result['status'] = action['status']
                        execution_result['output'] = action.get('output', None)
                        execution_result['error'] = action.get('error', None)
                        break
                    
                    # 检查是否需要使用工具
                    if 'tool' in action and 'params' in action:
                        tool_name = action['tool']
                        tool_params = action['params']
                        
                        # 检查工具是否可用
                        if tool_name in self.available_tools:
                            try:
                                # 执行工具
                                tool_module = self.available_tools[tool_name]
                                tool_result = tool_module.execute(**tool_params)
                                
                                # 记录使用的工具
                                execution_result['tools_used'].append({
                                    'tool': tool_name,
                                    'params': tool_params,
                                    'result': tool_result
                                })
                                
                                # 添加工具执行结果到对话历史
                                conversation_history.append({"role": "user", "content": f"工具执行结果:\n{json.dumps(tool_result, ensure_ascii=False, indent=2)}\n\n请继续执行或返回最终结果。"})
                            except Exception as e:
                                error_msg = f"工具执行失败: {tool_name}, 错误: {str(e)}"
                                logging.error(error_msg)
                                
                                # 添加错误信息到对话历史
                                conversation_history.append({"role": "user", "content": f"工具执行错误: {error_msg}\n\n请尝试其他方法或返回执行失败。"})
                        else:
                            # 工具不可用
                            conversation_history.append({"role": "user", "content": f"工具不可用: {tool_name}\n\n可用工具有: {', '.join(self.available_tools.keys())}\n\n请尝试其他方法或返回执行失败。"})
                    else:
                        # 响应格式不正确
                        conversation_history.append({"role": "user", "content": "请以正确的JSON格式返回执行结果或工具调用请求。"})
                    
                except json.JSONDecodeError:
                    # JSON解析失败
                    conversation_history.append({"role": "user", "content": "请以有效的JSON格式返回响应。"})
                
                current_turn += 1
            
            # 如果达到最大对话轮数但仍未完成
            if execution_result['status'] == 'pending':
                execution_result['status'] = 'failed'
                execution_result['error'] = '执行超过最大对话轮数'
            
            logging.info(f"执行Agent完成处理，状态: {execution_result['status']}")
            return execution_result
            
        except Exception as e:
            logging.error(f"执行Agent处理失败: {str(e)}")
            execution_result['status'] = 'failed'
            execution_result['error'] = str(e)
            return execution_result