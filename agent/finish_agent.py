#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
结束Agent模块 - 负责总结执行结果
"""

import os
import json
import logging
import openai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class FinishAgent:
    """
    结束Agent类 - 总结执行结果
    """
    
    def __init__(self):
        """
        初始化结束Agent
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_base = os.getenv('OPENAI_API_BASE')
        self.model = os.getenv('OPENAI_MODEL')
        
        # 设置OpenAI API
        openai.api_key = self.api_key
        if self.api_base and self.api_base != 'https://api.openai.com/v1':
            openai.api_base = self.api_base
        
        # 加载提示词
        self.system_prompt = self._load_prompt('finish_agent_prompt.txt')
    
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
            return """你是一个总结专家。你的任务是总结执行结果。
请根据所有步骤的执行情况，生成一个全面的总结报告。
总结应包括完成了哪些任务、创建了哪些文件、遇到了哪些问题以及最终结果。
请以JSON格式返回总结结果，包含总结内容和状态。"""
    
    def process(self, steps, steps_status, user_input):
        """
        处理执行结果，生成总结
        
        Args:
            steps (list): 所有步骤的列表
            steps_status (list): 所有步骤的执行状态
            user_input (str): 用户的原始输入
            
        Returns:
            dict: 总结结果，包含总结内容和状态
        """
        logging.info(f"结束Agent开始生成总结")
        
        try:
            # 构建提示词
            steps_info = []
            for i, (step, status) in enumerate(zip(steps, steps_status)):
                step_info = {
                    'step_number': step['step_number'],
                    'description': step['description'],
                    'expected_result': step['expected_result'],
                    'status': status['status'],
                    'result': status['result']
                }
                steps_info.append(step_info)
            
            prompt = f"用户需求: {user_input}\n\n执行步骤和结果:\n{json.dumps(steps_info, ensure_ascii=False, indent=2)}"
            
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
            logging.debug(f"结束Agent响应: {content}")
            
            # 尝试解析JSON
            try:
                summary_data = json.loads(content)
                
                # 验证总结格式
                validated_summary = {
                    'status': summary_data.get('status', 'completed'),
                    'summary': summary_data.get('summary', '未提供总结内容'),
                    'created_files': summary_data.get('created_files', []),
                    'issues': summary_data.get('issues', [])
                }
                
                logging.info(f"结束Agent成功生成总结")
                return validated_summary
                
            except json.JSONDecodeError as e:
                logging.error(f"解析结束Agent响应失败: {str(e)}")
                # 返回一个默认总结
                return {
                    'status': 'completed',
                    'summary': content,  # 使用原始内容作为总结
                    'created_files': [],
                    'issues': []
                }
                
        except Exception as e:
            logging.error(f"结束Agent处理失败: {str(e)}")
            # 返回一个默认总结
            return {
                'status': 'error',
                'summary': f"生成总结时出错: {str(e)}",
                'created_files': [],
                'issues': [f"总结生成错误: {str(e)}"] 
            }