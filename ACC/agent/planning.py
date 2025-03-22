"""规划Agent模块

该模块提供了规划Agent的实现，负责分析用户需求并创建详细的执行计划。
规划Agent是ACC系统的核心组件之一，它将用户的需求转化为可执行的任务列表。
"""

import json
import logging
import re

from typing import Dict, Any

from ACC.agent.base import BaseAgent
from ACC.prompt.planning import SYSTEM_PROMPT, FIRST_STEP_PROMPT

from ACC.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


# 在文件顶部添加以下导入
import os
from pathlib import Path


class PlanningAgent(BaseAgent):
    """规划Agent，负责分析用户需求并创建详细的执行计划"""

    def __init__(self):
        """初始化规划Agent"""
        # tools_config = get_tools_config()
        tools_config = ""
        tools_description = json.dumps(tools_config, ensure_ascii=False, indent=2)
        
        # 检查SYSTEM_PROMPT中的占位符
        logger.debug(f"SYSTEM_PROMPT内容: {SYSTEM_PROMPT[:100]}...")
        
        try:
            # 修改这里，直接使用SYSTEM_PROMPT，不进行格式化
            # 因为从prompt/planning.py中看，SYSTEM_PROMPT并不需要格式化参数
            super().__init__(name="planning", system_prompt=SYSTEM_PROMPT)
            logger.info("规划Agent初始化完成")
        except Exception as e:
            logger.error(f"规划Agent初始化失败: {e}")
            import traceback
            logger.error(f"初始化异常堆栈: {traceback.format_exc()}")
            raise

    def parse_json_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """专用JSON解析方法"""
        content = ""  # 初始化content变量，避免未绑定错误
        try:
            content = response.get("content", "").replace("\x00", "").strip()

            # 加强代码块去除逻辑（支持```json和```）
            cleaned = re.sub(r"^```(json)?|```$", "", content, flags=re.MULTILINE)

            # 处理中文引号问题
            cleaned = cleaned.replace(""", '"').replace(""", '"')

            return json.loads(cleaned, strict=False)
        except Exception as e:
            # 添加详细错误日志
            logger.error(f"规划结果解析失败: {str(e)}\n原始内容: {content[:500]}...")
            return {"error": f"JSON解析错误: {str(e)}", "raw_response": content}

    def _save_planning_md(self, content: str) -> str:
        """保存规划文件到ACC/memory/todo目录"""
        # 计算项目根目录（假设planning.py在ACC/agent目录）
        current_dir = Path(__file__).parent
        todo_dir = current_dir.parent / "memory" / "todo"
        todo_dir.mkdir(parents=True, exist_ok=True)

        file_path = todo_dir / "planning.md"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                # 确保内容中的换行符被正确处理
                f.write(content.replace("\\n", "\n"))
            logger.info(f"保存规划文件成功: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"保存规划文件失败: {e}")
            raise

    def run(self, user_input: str) -> Dict[str, Any]:
        """运行规划Agent"""
        logger.info(f"规划Agent开始处理用户输入: {user_input}")
    
        # 初始化response变量，避免未绑定错误
        response: Dict[str, Any] = {"content": ""}
    
        try:
            # 读取历史对话记录
            history = MemoryManager.read_json("history.json")
            
            # 重置消息列表
            self.reset_messages()
            
            # 添加历史对话到消息列表（只保留系统消息，跳过用户和助手消息）
            for msg in history:
                # 检查消息格式
                if not isinstance(msg, dict):
                    continue
                    
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "system":
                    # 只在第一次运行时保留系统提示
                    if not any(m["role"] == "system" for m in self.messages if isinstance(m, dict)):
                        self.messages.append(msg)
                # 跳过用户和助手的历史消息
                elif role in ["user", "assistant"]:
                    continue
                # 处理其他不支持的角色
                else:
                    # 对于其他不支持的角色，默认转为系统消息
                    self.messages.append(
                        {
                            "role": "system",
                            "content": f"{role}: {content}",
                        }
                    )
                    
            self.add_message("user", FIRST_STEP_PROMPT.format(user_input=user_input))
    
            logger.info("🔄 正在向LLM发送规划请求...")
            response = self.send_to_llm()
            logger.info("✅ 成功接收LLM规划响应")
    
            planning_result = self.parse_json_response(response)
    
            # 检查是否有错误
            if "error" in planning_result:
                logger.error(f"规划结果解析出错: {planning_result['error']}")
                # 尝试从原始响应中提取task_structure
                raw_response = planning_result.get("raw_response", "")
                task_structure_match = re.search(
                    r'"task_structure":\s*"(.*?)(?:"\s*}|"\s*,)',
                    raw_response,
                    re.DOTALL,
                )
                if task_structure_match:
                    task_structure = task_structure_match.group(1)
                    # 处理转义字符
                    task_structure = task_structure.replace("\\n", "\n").replace(
                        '\\"', '"'
                    )
                    self._save_planning_md(task_structure)
                    logger.info("成功从原始响应中提取并保存task_structure")
                else:
                    logger.error("无法从原始响应中提取task_structure")
                    return planning_result
            else:
                # 修复任务结构访问方式
                task_structure = None
                
                # 尝试从不同位置获取task_structure
                if "tasks" in planning_result:
                    tasks = planning_result["tasks"]
                    
                    # 如果tasks是字典
                    if isinstance(tasks, dict):
                        # 尝试直接从tasks字典中获取task_structure
                        if "task_structure" in tasks:
                            task_structure = tasks["task_structure"]
                        else:
                            # 尝试从tasks的第一个子项中获取
                            for key, value in tasks.items():
                                if isinstance(value, dict) and "task_structure" in value:
                                    task_structure = value["task_structure"]
                                    break
                    
                    # 如果tasks是列表
                    elif isinstance(tasks, list) and len(tasks) > 0:
                        # 尝试从第一个元素获取
                        if isinstance(tasks[0], dict) and "task_structure" in tasks[0]:
                            task_structure = tasks[0]["task_structure"]
            
                # 如果上述方法都无法获取task_structure，尝试直接从planning_result获取
                if task_structure is None and "task_structure" in planning_result:
                    task_structure = planning_result["task_structure"]
                    
                # 如果找到了task_structure，保存它
                if task_structure:
                    self._save_planning_md(task_structure)
                    logger.info(f"成功保存task_structure到planning.md")
                else:
                    # 如果无法找到task_structure，创建一个基本的任务结构
                    logger.warning("无法找到task_structure，创建基本任务结构")
                    basic_structure = f"# 用户需求: {user_input}\n\n## 1. 任务\n- [ ] 1.1 执行用户请求"
                    self._save_planning_md(basic_structure)
    
            self.reset_messages()
            return planning_result
        except Exception as e:
            self.reset_messages()
            logger.error(f"规划流程失败: {e}")
            import traceback
            logger.debug(f"异常堆栈: {traceback.format_exc()}")
            return {
                "error": f"规划流程失败: {str(e)}",
                "raw_response": response.get("content", ""),
            }
