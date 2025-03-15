#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
agent/execution_agent.py - 执行Agent

该模块负责执行分析Agent生成的执行计划，是工作流的第三步。
"""

import os
import json
import logging
import importlib
from typing import Dict, Any, List
from .base_agent import BaseAgent

class ExecutionAgent(BaseAgent):
    """
    执行Agent类，负责执行分析Agent生成的执行计划
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化执行Agent
        
        Args:
            config: 系统配置信息
        """
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.available_plugins = self._load_available_plugins()
    
    def _load_available_plugins(self) -> Dict[str, Any]:
        """
        加载可用的插件
        
        Returns:
            Dict[str, Any]: 可用插件字典
        """
        plugins = {}
        plugins_dir = 'plugins'
        
        if not os.path.exists(plugins_dir):
            self.logger.warning(f"插件目录 {plugins_dir} 不存在")
            return plugins
        
        # 遍历插件目录
        for item in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, item)
            
            # 只处理目录
            if os.path.isdir(plugin_path) and not item.startswith('_'):
                try:
                    # 尝试导入插件模块
                    module_path = f"plugins.{item}.plugin"
                    plugin_module = importlib.import_module(module_path)
                    
                    # 获取插件信息
                    plugin_info = getattr(plugin_module, 'PLUGIN_INFO', None)
                    if plugin_info:
                        plugins[item] = {
                            'name': plugin_info.get('name', item),
                            'description': plugin_info.get('description', ''),
                            'version': plugin_info.get('version', '1.0.0'),
                            'module': plugin_module
                        }
                        self.logger.info(f"加载插件: {item} v{plugin_info.get('version', '1.0.0')}")
                except Exception as e:
                    self.logger.error(f"加载插件 {item} 失败: {str(e)}")
        
        return plugins
    
    def get_system_prompt(self) -> str:
        """
        获取系统提示词
        
        Returns:
            str: 系统提示词
        """
        prompt_path = os.path.join('agent', 'prompts', 'execution_agent_prompt.txt')
        
        # 构建可用插件信息
        plugins_info = "\n可用插件列表:\n"
        for plugin_name, plugin_data in self.available_plugins.items():
            plugins_info += f"- {plugin_data['name']} (v{plugin_data['version']}): {plugin_data['description']}\n"
        
        if os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
                # 替换插件信息占位符
                return prompt.replace('{PLUGINS_INFO}', plugins_info)
        else:
            # 默认提示词
            return f"""
你是一个专业的执行专家，负责执行分析Agent生成的执行计划。

{plugins_info}

你的任务是：
1. 仔细分析执行计划中的操作
2. 确定每个操作需要使用的工具或插件
3. 按照正确的顺序执行每个操作
4. 记录执行过程和结果
5. 处理可能出现的错误和异常情况

如果你需要使用插件，请按照以下JSON格式回复：
{{
  "plugin": "插件名称",
  "action": "插件操作",
  "parameters": {{插件操作所需参数}}
}}

执行完成后，请以JSON格式返回执行结果，格式如下：
{{
  "step_id": 执行的步骤ID,
  "execution_results": [
    {{
      "operation_id": 操作ID,
      "status": "success|failed",
      "result": "执行结果",
      "error": "如果失败，错误信息"
    }},
    ...
  ],
  "overall_status": "success|partial_success|failed",
  "summary": "执行总结"
}}

记住，你的输出将直接被系统解析为JSON，不要包含任何其他文本。
"""
    
    def process(self, execution_plan: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理执行计划，执行操作
        
        Args:
            execution_plan: 分析Agent生成的执行计划
            conversation_history: 对话历史
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        step_id = execution_plan.get('step_id')
        operations = execution_plan.get('execution_plan', {}).get('operations', [])
        
        self.logger.info(f"开始执行步骤 {step_id} 的操作，共 {len(operations)} 个操作")
        
        # 构建消息
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"请执行以下计划:\n{json.dumps(execution_plan, ensure_ascii=False, indent=2)}\n\n以下是之前的对话历史，可能对你的执行有帮助:\n{json.dumps(conversation_history[-5:], ensure_ascii=False, indent=2)}"}
        ]
        
        # 执行操作可能需要多轮对话
        execution_results = []
        overall_status = "success"
        conversation = messages.copy()
        
        try:
            # 第一轮对话
            response = self.call_api(conversation, temperature=0.2)
            result = self.process_response(response)
            
            # 检查是否需要使用插件
            while 'plugin' in result:
                plugin_name = result.get('plugin')
                action = result.get('action')
                parameters = result.get('parameters', {})
                
                # 执行插件操作
                plugin_result = self._execute_plugin(plugin_name, action, parameters)
                
                # 添加插件执行结果到对话
                conversation.append({"role": "assistant", "content": json.dumps(result, ensure_ascii=False)})
                conversation.append({"role": "user", "content": f"插件执行结果:\n{json.dumps(plugin_result, ensure_ascii=False, indent=2)}\n\n请继续执行或返回最终结果。"})
                
                # 继续对话
                response = self.call_api(conversation, temperature=0.2)
                result = self.process_response(response)
            
            # 最终结果
            if 'execution_results' in result:
                execution_results = result.get('execution_results', [])
                overall_status = result.get('overall_status', 'failed')
            else:
                raise ValueError("执行Agent返回的结果格式不正确")
                
        except Exception as e:
            self.logger.error(f"执行操作失败: {str(e)}")
            overall_status = "failed"
            execution_results = [{
                "operation_id": op.get('operation_id', i+1),
                "status": "failed",
                "result": "",
                "error": f"执行失败: {str(e)}"
            } for i, op in enumerate(operations)]
        
        # 构建最终结果
        final_result = {
            "step_id": step_id,
            "execution_results": execution_results,
            "overall_status": overall_status,
            "summary": f"步骤 {step_id} 执行{'成功' if overall_status == 'success' else '部分成功' if overall_status == 'partial_success' else '失败'}"
        }
        
        self.logger.info(f"步骤 {step_id} 执行完成，状态: {overall_status}")
        return final_result
    
    def _execute_plugin(self, plugin_name: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行插件操作
        
        Args:
            plugin_name: 插件名称
            action: 操作名称
            parameters: 操作参数
            
        Returns:
            Dict[str, Any]: 插件执行结果
        """
        self.logger.info(f"执行插件 {plugin_name} 的 {action} 操作")
        
        try:
            # 检查插件是否存在
            if plugin_name not in self.available_plugins:
                return {
                    "status": "failed",
                    "error": f"插件 {plugin_name} 不存在"
                }
            
            # 获取插件模块
            plugin_module = self.available_plugins[plugin_name]['module']
            
            # 检查操作是否存在
            if not hasattr(plugin_module, action):
                return {
                    "status": "failed",
                    "error": f"插件 {plugin_name} 不支持 {action} 操作"
                }
            
            # 执行操作
            plugin_action = getattr(plugin_module, action)
            result = plugin_action(**parameters)
            
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"执行插件 {plugin_name} 的 {action} 操作失败: {str(e)}")
            return {
                "status": "failed",
                "error": f"执行失败: {str(e)}"
            }