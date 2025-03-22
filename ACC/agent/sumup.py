"""总结Agent模块

该模块提供了总结Agent的实现，负责分析和总结系统执行的所有操作历史。
总结Agent是ACC系统的收尾组件，它将操作历史转化为可读的总结报告。
"""

import json
import logging
import os
import glob
from typing import Dict, Any, List
from pathlib import Path

from ACC.agent.base import BaseAgent
from ACC.prompt.sumup import SYSTEM_PROMPT, FIRST_STEP_PROMPT
from ACC.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class SumupAgent(BaseAgent):
    """总结Agent，负责分析和总结系统执行的所有操作历史"""

    def __init__(self):
        """初始化总结Agent"""
        super().__init__(name="sumup", system_prompt=SYSTEM_PROMPT)
        logger.info("总结Agent初始化完成")
        
        # 确保操作历史记录目录存在
        self._ensure_operation_history_dir()
        
    def _ensure_operation_history_dir(self):
        """确保操作历史记录目录存在"""
        self.operation_history_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "memory", 
            "operation_generalization"
        )
        if not os.path.exists(self.operation_history_dir):
            os.makedirs(self.operation_history_dir, exist_ok=True)
            logger.info(f"创建操作历史记录目录: {self.operation_history_dir}")
        logger.debug(f"操作历史记录目录: {self.operation_history_dir}")

    def _get_all_operation_history(self) -> List[Dict]:
        """获取所有操作历史记录
        
        Returns:
            按任务编号排序的所有操作历史记录列表
        """
        try:
            # 获取所有操作历史文件
            history_files = glob.glob(os.path.join(self.operation_history_dir, "*.json"))
            
            # 按文件名排序（文件名格式为：任务编号.json）
            history_files.sort(key=lambda x: self._extract_task_number(os.path.basename(x)))
            
            all_history = []
            for file_path in history_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        history = json.load(f)
                        
                    # 添加任务编号信息
                    task_number = self._extract_task_number(os.path.basename(file_path))
                    all_history.append({
                        "task_number": task_number,
                        "history": history
                    })
                except Exception as e:
                    logger.error(f"读取操作历史文件失败: {file_path}, 错误: {e}")
            
            return all_history
        except Exception as e:
            logger.error(f"获取所有操作历史记录失败: {e}")
            return []
    
    def _extract_task_number(self, filename: str) -> str:
        """从文件名中提取任务编号
        
        Args:
            filename: 文件名，格式为：任务编号.json
            
        Returns:
            任务编号，如：1.1
        """
        # 文件名格式为：1_1.json，需要转换为1.1
        try:
            name_without_ext = os.path.splitext(filename)[0]
            return name_without_ext.replace("_", ".")
        except Exception:
            return filename
    
    def _format_operation_history(self, all_history: List[Dict]) -> str:
        """格式化操作历史记录为可读文本
        
        Args:
            all_history: 所有操作历史记录
            
        Returns:
            格式化后的操作历史记录文本
        """
        formatted_text = "# 操作历史记录\n\n"
        
        for task in all_history:
            task_number = task.get("task_number", "未知任务")
            history = task.get("history", [])
            
            formatted_text += f"## 任务 {task_number}\n\n"
            
            for idx, record in enumerate(history):
                role = record.get("role", "")
                content = record.get("content", "")
                
                if role == "assistant":
                    # 尝试解析JSON内容
                    try:
                        # 去除可能的代码块标记
                        clean_content = content
                        if "```json" in content and "```" in content:
                            clean_content = content.split("```json")[-1].split("```")[0].strip()
                        
                        data = json.loads(clean_content)
                        
                        # 提取关键信息
                        todo_item = data.get("todo_item", "未知任务项")
                        step_summary = data.get("step_summary", "")
                        action_type = data.get("action_type", "")
                        explanation = data.get("explanation", "")
                        success = data.get("success", False)
                        
                        formatted_text += f"### 步骤 {idx+1}: {todo_item}\n\n"
                        formatted_text += f"- **摘要**: {step_summary}\n"
                        formatted_text += f"- **操作类型**: {action_type}\n"
                        formatted_text += f"- **说明**: {explanation}\n"
                        formatted_text += f"- **状态**: {'成功' if success else '未完成'}\n\n"
                    except json.JSONDecodeError:
                        # 如果不是JSON格式，直接使用原始内容
                        formatted_text += f"### 步骤 {idx+1}\n\n"
                        formatted_text += f"- **内容**: {content}\n\n"
                elif role == "tool_result":
                    formatted_text += f"### 工具执行结果\n\n"
                    formatted_text += f"```\n{content}\n```\n\n"
            
            formatted_text += "---\n\n"
        
        return formatted_text

    def run(self) -> Dict[str, Any]:
        """运行总结Agent，生成系统执行总结报告"""
        logger.info("开始生成系统执行总结报告")
        
        try:
            # 获取所有操作历史记录
            all_history = self._get_all_operation_history()
            
            if not all_history:
                logger.warning("未找到任何操作历史记录")
                return {
                    "status": "warning",
                    "message": "未找到任何操作历史记录",
                    "summary": "系统未执行任何操作或未生成操作历史记录。"
                }
            
            # 格式化操作历史记录
            formatted_history = self._format_operation_history(all_history)
            
            # 重置消息列表
            self.reset_messages()
            
            # 添加用户提示
            self.add_message(
                "user", FIRST_STEP_PROMPT.format(operation_history=formatted_history)
            )
            
            # 获取LLM响应
            logger.info("🔄 正在生成系统执行总结报告...")
            response = self.send_to_llm()
            
            # 保存总结报告
            summary_content = response.get("content", "")
            summary_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "memory",
                "summary.md"
            )
            
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary_content)
            
            logger.info(f"系统执行总结报告已保存至: {summary_path}")
            
            return {
                "status": "success",
                "message": "系统执行总结报告生成成功",
                "summary": summary_content,
                "summary_path": summary_path
            }
        except Exception as e:
            logger.error(f"生成系统执行总结报告失败: {str(e)}")
            import traceback
            logger.debug(f"异常堆栈: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"生成系统执行总结报告失败: {str(e)}",
                "summary": None
            }