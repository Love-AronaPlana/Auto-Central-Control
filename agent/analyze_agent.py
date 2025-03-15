#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
分析具体操作步骤Agent模块 - 负责判断如何执行每个步骤
"""

import os
import json
import logging
import openai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class AnalyzeAgent:
    """
    分析具体操作步骤Agent类 - 判断如何执行每个步骤
    """
    
    def __init__(self):
        """
        初始化分析Agent
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_base = os.getenv('OPENAI_API_BASE')
        self.model = os.getenv('OPENAI_MODEL')
        
        # 设置OpenAI API
        openai.api_key = self.api_key
        if self.api_base and self.api_base != 'https://api.openai.com/v1':
            openai.api_base = self.api_base
        
        # 加载提示词
        self.system_prompt = self._load_prompt('analyze_agent_prompt.txt')
    
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
            return """你是一个操作分析专家。你的任务是分析如何执行给定的步骤。
请详细说明执行步骤的方法，包括需要使用的工具、操作顺序和预期结果。
请以JSON格式返回分析结果，包含执行方法、所需工具和预期结果。"""
    
    def process(self, step, user_input):
        """
        处理步骤，分析如何执行
        
        Args:
            step (dict): 要执行的步骤，包含步骤编号、描述和预期结果
            user_input (str): 用户的原始输入
            
        Returns:
            dict: 执行计划，包含执行方法、所需工具和预期结果
        """
        logging.info(f"分析Agent开始处理步骤: {step['description']}")
        
        try:
            # 构建提示词
            prompt = f"用户需求: {user_input}\n\n步骤: {step['description']}\n预期结果: {step['expected_result']}"
            
            # 调用OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            
            # 解析响应
            content = response.choices[0].message.content
            logging.debug(f"分析Agent响应: {content}")
            
            # 尝试解析JSON
            try:
                execution_plan = json.loads(content)
                
                # 验证执行计划格式
                validated_plan = {
                    'step': step,
                    'method': execution_plan.get('method', '未提供执行方法'),
                    'tools': execution_plan.get('tools', []),
                    'expected_result': execution_plan.get('expected_result', step['expected_result']),
                    'summary': execution_plan.get('summary', '未提供执行摘要')
                }
                
                logging.info(f"分析Agent成功生成执行计划")
                return validated_plan
                
            except json.JSONDecodeError as e:
                logging.error(f"解析分析Agent响应失败: {str(e)}")
                # 返回一个默认执行计划
                return {
                    'step': step,
                    'method': '直接执行步骤',
                    'tools': [],
                    'expected_result': step['expected_result'],
                    'summary': '执行步骤以达到预期结果'
                }
                
        except Exception as e:
            logging.error(f"分析Agent处理失败: {str(e)}")
            # 返回一个默认执行计划
            return {
                'step': step,
                'method': '直接执行步骤',
                'tools': [],
                'expected_result': step['expected_result'],
                'summary': '执行步骤以达到预期结果'
            }