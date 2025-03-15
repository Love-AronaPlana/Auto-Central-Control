#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
步骤Agent模块 - 负责将用户的操作需求分解为多个详细步骤
"""

import os
import json
import logging
import openai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class StepAgent:
    """
    步骤Agent类 - 将用户的操作需求分解为多个详细步骤
    """
    
    def __init__(self):
        """
        初始化步骤Agent
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_base = os.getenv('OPENAI_API_BASE')
        self.model = os.getenv('OPENAI_MODEL')
        
        # 设置OpenAI API
        openai.api_key = self.api_key
        if self.api_base and self.api_base != 'https://api.openai.com/v1':
            openai.api_base = self.api_base
        
        # 加载提示词
        self.system_prompt = self._load_prompt('step_agent_prompt.txt')
    
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
            return """你是一个步骤分解专家。你的任务是将用户的操作需求分解为多个详细的、可执行的步骤。
每个步骤应该足够具体，以便后续的Agent能够理解如何执行。
请以JSON格式返回步骤列表，每个步骤包含步骤编号、描述和预期结果。"""
    
    def process(self, user_input):
        """
        处理用户输入，将操作需求分解为多个步骤
        
        Args:
            user_input (str): 用户的操作需求
            
        Returns:
            list: 步骤列表，每个步骤是一个字典，包含步骤编号、描述和预期结果
        """
        logging.info("步骤Agent开始处理用户输入")
        
        try:
            # 调用OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
            )
            
            # 解析响应
            content = response.choices[0].message.content
            logging.debug(f"步骤Agent响应: {content}")
            
            # 尝试解析JSON
            try:
                steps_data = json.loads(content)
                # 确保返回的是列表
                if isinstance(steps_data, dict) and 'steps' in steps_data:
                    steps = steps_data['steps']
                else:
                    steps = steps_data
                
                # 验证步骤格式
                validated_steps = []
                for i, step in enumerate(steps):
                    validated_step = {
                        'step_number': step.get('step_number', i + 1),
                        'description': step.get('description', '未提供描述'),
                        'expected_result': step.get('expected_result', '未提供预期结果')
                    }
                    validated_steps.append(validated_step)
                
                logging.info(f"步骤Agent成功分解任务为 {len(validated_steps)} 个步骤")
                return validated_steps
                
            except json.JSONDecodeError as e:
                logging.error(f"解析步骤Agent响应失败: {str(e)}")
                # 返回一个默认步骤
                return [{
                    'step_number': 1,
                    'description': '执行用户请求的操作',
                    'expected_result': '完成用户请求'
                }]
                
        except Exception as e:
            logging.error(f"步骤Agent处理失败: {str(e)}")
            # 返回一个默认步骤
            return [{
                'step_number': 1,
                'description': '执行用户请求的操作',
                'expected_result': '完成用户请求'
            }]