#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
复查Agent模块 - 负责检查执行操作是否有错误
"""

import os
import json
import logging
import openai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class ReviewAgent:
    """
    复查Agent类 - 检查执行操作是否有错误
    """
    
    def __init__(self):
        """
        初始化复查Agent
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_base = os.getenv('OPENAI_API_BASE')
        self.model = os.getenv('OPENAI_MODEL')
        
        # 设置OpenAI API
        openai.api_key = self.api_key
        if self.api_base and self.api_base != 'https://api.openai.com/v1':
            openai.api_base = self.api_base
        
        # 加载提示词
        self.system_prompt = self._load_prompt('review_agent_prompt.txt')
    
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
            return """你是一个复查专家。你的任务是检查执行操作是否有错误。
请仔细分析执行结果，判断是否达到了预期目标，是否存在错误或异常。
如果发现错误，请详细描述错误的位置和内容。
请以JSON格式返回复查结果，包含状态（成功/错误）、错误信息（如有）和建议（如有）。"""
    
    def process(self, execution_result, step):
        """
        处理执行结果，检查是否有错误
        
        Args:
            execution_result (dict): 执行结果，包含状态、输出和错误信息
            step (dict): 原始步骤，包含步骤编号、描述和预期结果
            
        Returns:
            dict: 复查结果，包含状态、错误信息和建议
        """
        logging.info(f"复查Agent开始检查执行结果")
        
        try:
            # 构建提示词
            prompt = f"步骤: {step['description']}\n预期结果: {step['expected_result']}\n\n执行结果:\n{json.dumps(execution_result, ensure_ascii=False, indent=2)}"
            
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
            logging.debug(f"复查Agent响应: {content}")
            
            # 尝试解析JSON
            try:
                review_result = json.loads(content)
                
                # 验证复查结果格式
                validated_result = {
                    'status': review_result.get('status', 'unknown'),
                    'error_message': review_result.get('error_message', None),
                    'suggestions': review_result.get('suggestions', None),
                    'execution_result': execution_result
                }
                
                # 确保状态值为标准格式
                if validated_result['status'].lower() in ['success', 'successful', 'succeeded', 'ok', 'pass', 'passed']:
                    validated_result['status'] = 'success'
                elif validated_result['status'].lower() in ['error', 'fail', 'failed', 'failure', 'problem', 'issue']:
                    validated_result['status'] = 'error'
                else:
                    # 根据执行结果状态和是否有错误信息来判断
                    if execution_result['status'] == 'completed' and not validated_result['error_message']:
                        validated_result['status'] = 'success'
                    else:
                        validated_result['status'] = 'error'
                
                logging.info(f"复查Agent完成检查，状态: {validated_result['status']}")
                return validated_result
                
            except json.JSONDecodeError as e:
                logging.error(f"解析复查Agent响应失败: {str(e)}")
                # 返回一个默认复查结果
                return {
                    'status': 'error' if execution_result['status'] != 'completed' else 'success',
                    'error_message': f"无法解析复查结果: {str(e)}" if execution_result['status'] != 'completed' else None,
                    'suggestions': None,
                    'execution_result': execution_result
                }
                
        except Exception as e:
            logging.error(f"复查Agent处理失败: {str(e)}")
            # 返回一个默认复查结果
            return {
                'status': 'error',
                'error_message': f"复查过程出错: {str(e)}",
                'suggestions': None,
                'execution_result': execution_result
            }