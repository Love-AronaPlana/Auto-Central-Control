#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复错误Agent模块 - 负责修复执行过程中的错误
"""

import os
import json
import logging
import openai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class FixAgent:
    """
    修复错误Agent类 - 修复执行过程中的错误
    """
    
    def __init__(self):
        """
        初始化修复Agent
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_base = os.getenv('OPENAI_API_BASE')
        self.model = os.getenv('OPENAI_MODEL')
        
        # 设置OpenAI API
        openai.api_key = self.api_key
        if self.api_base and self.api_base != 'https://api.openai.com/v1':
            openai.api_base = self.api_base
        
        # 加载提示词
        self.system_prompt = self._load_prompt('fix_agent_prompt.txt')
    
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
            return """你是一个错误修复专家。你的任务是修复执行过程中的错误。
请根据错误信息和执行结果，分析错误原因并提出修复方案。
请以JSON格式返回修复结果，包含修复后的状态、修复方法和修复后的输出。"""
    
    def process(self, review_result, execution_result, step):
        """
        处理复查结果，修复错误
        
        Args:
            review_result (dict): 复查结果，包含状态、错误信息和建议
            execution_result (dict): 执行结果，包含状态、输出和错误信息
            step (dict): 原始步骤，包含步骤编号、描述和预期结果
            
        Returns:
            dict: 修复结果，包含状态、输出和错误信息
        """
        logging.info(f"修复Agent开始处理错误")
        
        # 初始化修复结果（基于执行结果）
        fix_result = execution_result.copy()
        
        try:
            # 构建提示词
            prompt = f"步骤: {step['description']}\n预期结果: {step['expected_result']}\n\n执行结果:\n{json.dumps(execution_result, ensure_ascii=False, indent=2)}\n\n复查结果:\n{json.dumps(review_result, ensure_ascii=False, indent=2)}"
            
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
            logging.debug(f"修复Agent响应: {content}")
            
            # 尝试解析JSON
            try:
                fix_plan = json.loads(content)
                
                # 更新修复结果
                fix_result['status'] = 'fixed'
                fix_result['output'] = fix_plan.get('output', fix_result.get('output'))
                fix_result['error'] = None  # 清除错误信息
                fix_result['fix_method'] = fix_plan.get('fix_method', '未提供修复方法')
                fix_result['fix_details'] = fix_plan.get('fix_details', '未提供修复详情')
                
                logging.info(f"修复Agent完成修复")
                return fix_result
                
            except json.JSONDecodeError as e:
                logging.error(f"解析修复Agent响应失败: {str(e)}")
                # 返回一个默认修复结果
                fix_result['status'] = 'failed'
                fix_result['error'] = f"无法解析修复结果: {str(e)}"
                return fix_result
                
        except Exception as e:
            logging.error(f"修复Agent处理失败: {str(e)}")
            # 返回一个默认修复结果
            fix_result['status'] = 'failed'
            fix_result['error'] = f"修复过程出错: {str(e)}"
            return fix_result