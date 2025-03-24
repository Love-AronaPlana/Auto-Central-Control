"""操作Agent模块

该模块提供了操作Agent的实现，负责根据细化步骤执行具体代码操作。
操作Agent是ACC系统的执行组件，它将细化步骤转化为具体的代码操作。
"""

import json
import logging
import os#
from typing import Dict, Any, Optional, List

from ACC.agent.base import BaseAgent

# 修复导入，添加WORKSPACE_ABS_PATH
from ACC.prompt.operate import (
    SYSTEM_PROMPT,
    FIRST_STEP_PROMPT,
    TOOL_STEP_PROMPT,
    WORKSPACE_ABS_PATH,
    tools_description,  # 导入tools_description变量
)
from ACC.memory.memory_manager import MemoryManager
from ACC.tool.base import execute_tool, ToolRegistry

import re
logger = logging.getLogger(__name__)


class OperateAgent(BaseAgent):
    """操作Agent，负责根据细化步骤执行具体代码操作"""

    def __init__(self):
        """初始化操作Agent"""
        try:
            # 直接使用SYSTEM_PROMPT，不进行格式化
            super().__init__(name="operate", system_prompt=SYSTEM_PROMPT)
            logger.info("操作Agent初始化完成")
            
            # 确保workspace目录存在
            self._ensure_workspace_dir()
            
            # 确保操作历史记录目录存在
            self._ensure_operation_history_dir()
        except Exception as e:
            logger.error(f"操作Agent初始化失败: {e}")
            import traceback
            logger.error(f"初始化异常堆栈: {traceback.format_exc()}")
            raise

    # 重写parse_json_response方法，增强对特殊字符的处理能力
    def parse_json_response(self, response: Dict[str, Any]) -> Any:
        """解析LLM响应中的JSON内容
        
        Args:
            response: LLM响应
            
        Returns:
            解析后的JSON对象
        """
        try:
            content = response.get("content", "")
            
            # 提取JSON内容
            json_content = content
            
            # 如果内容被包裹在```json和```之间，提取出来
            if "```json" in content and "```" in content:
                pattern = r"```json\s*([\s\S]*?)\s*```"
                match = re.search(pattern, content)
                if match:
                    json_content = match.group(1)
            
            # 处理特殊的转义字符问题
            # 1. 先替换掉正则表达式中常见的问题模式
            # 处理 href=[\"\\'] 这种模式
            json_content = re.sub(r'href=\[(\\+)"(\\+)\'\]', r'href=[\\\\"\\\\\'"]', json_content)
            # 处理 [\"\\'] 这种模式
            json_content = re.sub(r'\[(\\+)"(\\+)\'\]', r'[\\\\"\\\\\'"]', json_content)
            # 处理其他可能的转义问题
            json_content = json_content.replace(r'\\\"', r'\\"').replace(r'\\\'', r'\\\'')
            
            # 2. 尝试解析JSON
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON失败: {e}")
            logger.error(f"原始内容: {content}")
            # 如果解析失败，返回原始内容
            return content
        except Exception as e:
            logger.error(f"解析响应时出错: {e}")
            return content

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

    def _clean_operate_history(self, task_number=None):
        """清空操作历史记录
        
        Args:
            task_number: 任务编号，如果为None则清空所有历史记录
        """
        try:
            if task_number is None:
                # 清空所有历史记录
                import glob
                history_files = glob.glob(os.path.join(self.operation_history_dir, "*.json"))
                for file_path in history_files:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("[]")
                logger.info(f"清空所有操作历史记录完成，共{len(history_files)}个文件")
                logger.debug(f"已清空的历史记录文件: {history_files}")
            else:
                # 清空指定任务的历史记录
                history_file = self._get_history_file_path(task_number)
                with open(history_file, "w", encoding="utf-8") as f:
                    f.write("[]")
                logger.info(f"清空任务 {task_number} 的操作历史记录完成")
                logger.debug(f"已清空的历史记录文件: {history_file}")
        except Exception as e:
            logger.error(f"清空操作历史记录失败: {e}")
            import traceback
            logger.debug(f"清空操作历史记录异常堆栈: {traceback.format_exc()}")

    def _ensure_workspace_dir(self):
        """确保workspace目录存在"""
        workspace_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "workspace"
        )
        if not os.path.exists(workspace_dir):
            os.makedirs(workspace_dir, exist_ok=True)
            logger.info(f"创建workspace目录: {workspace_dir}")

    def _get_file_content(self, file_path: str) -> Optional[str]:
        """获取文件内容"""
        try:
            memory_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "memory"
            )
            full_path = os.path.join(memory_dir, file_path)

            if not os.path.exists(full_path):
                logger.error(f"文件不存在: {full_path}")
                return None

            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return None

    def _update_refinement_file(self, file_path: str, updated_content: str) -> bool:
        """更新细化文件内容"""
        try:
            memory_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "memory"
            )
            full_path = os.path.join(memory_dir, file_path)

            if not os.path.exists(full_path):
                logger.error(f"文件不存在: {full_path}")
                return False

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            logger.info(f"更新细化文件成功: {full_path}")
            return True
        except Exception as e:
            logger.error(f"更新细化文件失败: {e}")
            return False

    def _execute_tool_action(
        self, tool_name: str, tool_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行工具操作"""
        logger.info(f"执行工具操作: {tool_name}, 参数: {tool_params}")

        # 检查工具是否存在
        if not ToolRegistry.get_tool(tool_name):
            logger.error(f"工具不存在: {tool_name}")
            return {"error": f"工具不存在: {tool_name}"}

        # 执行工具
        try:
            result = execute_tool(tool_name, **tool_params)
            logger.info(f"工具执行结果: {result}")
            return result
        except Exception as e:
            logger.error(f"工具执行失败: {e}")
            return {"error": f"工具执行失败: {e}"}

    def handle_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理工具调用

        Args:
            tool_calls: 工具调用列表

        Returns:
            工具执行结果
        """
        if not tool_calls or len(tool_calls) == 0:
            return {"error": "没有工具调用"}

        # 目前只处理第一个工具调用
        tool_call = tool_calls[0]
        tool_name = tool_call.get("function", {}).get("name")
        tool_params_str = tool_call.get("function", {}).get("arguments", "{}")

        try:
            tool_params = json.loads(tool_params_str)
            return self._execute_tool_action(tool_name, tool_params)
        except json.JSONDecodeError:
            logger.error(f"工具参数解析失败: {tool_params_str}")
            return {"error": f"工具参数解析失败: {tool_params_str}"}
        except Exception as e:
            logger.error(f"工具调用处理失败: {e}")
            return {"error": f"工具调用处理失败: {str(e)}"}

    def run(self, user_input: str) -> Dict[str, Any]:
        """运行操作Agent
        
        Args:
            user_input: 用户输入，在这里是细化文件路径
        
        Returns:
            操作结果字典
        """
        refinement_file = user_input  # 将参数重命名为符合实际用途的变量
    
        try:
            # 读取细化文件内容
            refinement_content = MemoryManager.read_file(refinement_file)
    
            # 读取规划文件内容
            planning_content = MemoryManager.read_file("todo/planning.md")
            
            # 获取当前任务编号
            task_number = "unknown"
            # 修改正则表达式以匹配文件名中的任务编号
            if task_number_match := re.search(r"refinement[/\\](\d+_\d+)\.md$", refinement_file):
                # 将下划线替换回点号，转换为标准格式（如：1_2 -> 1.2）
                task_number = task_number_match.group(1).replace('_', '.')
            else:
                # 使用时间戳作为备用文件名
                from datetime import datetime
                task_number = f"unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                logger.warning(f"无法从文件名获取任务编号: {refinement_file}，使用时间戳: {task_number}")
    
            # 读取操作历史记录
            operation_history = self._read_operation_history(task_number)
    
            # 重置消息列表
            self.reset_messages()
        
            # 添加历史对话到消息列表
            system_added = False  # 添加标志变量，跟踪是否已添加系统消息
            for msg in operation_history:
                if not isinstance(msg, dict):
                    continue
        
                role = msg.get("role", "")
                content = msg.get("content", "")
        
                # 只添加一次系统提示
                if role == "system":
                    if not system_added:
                        self.messages.append(msg)
                        system_added = True
                # 添加工具结果和助手消息
                elif role in ["tool_result", "assistant"]:
                    self.messages.append(msg)
                # 跳过用户消息，因为我们会重新构建提示词
                elif role == "user":
                    continue
    
            # 在构建提示词并添加到消息列表后，保存用户消息到操作历史记录
            prompt = FIRST_STEP_PROMPT.format(
                refinement_content=refinement_content,
                planning_content=planning_content,
                WORKSPACE_ABS_PATH=WORKSPACE_ABS_PATH,
            )
            self.add_message("user", prompt)
    
            # 添加：保存用户消息到操作历史记录
            operation_history.append({"role": "user", "content": prompt})
    
            # 发送请求
            logger.info("🔄 正在向LLM发送操作请求...")
            response = self.send_to_llm()
    
            # 解析响应
            result = self.parse_json_response(response)
    
            # 如果解析失败，添加默认值防止后续处理出错
            if not isinstance(result, dict):
                logger.error(f"解析响应失败，响应内容: {response}")
                return {"error": f"解析响应失败: {response}", "success": False}
    
            # 根据action_type处理不同类型的操作
            action_type = result.get("action_type", "none")
    
            if action_type == "tool":
                # 处理工具调用
                tool_name = result.get("tool_name")
                tool_params = result.get("tool_params", {})
    
                if tool_name:
                    # 如果是写入文件相关的工具，检查是否需要处理文件已存在的情况
                    if tool_name in [
                        "create_file",
                        "write_file",
                    ] and "zuowen.txt" in str(tool_params.get("file_path", "")):
                        # 对于zuowen.txt文件，添加覆盖参数
                        if tool_name == "create_file":
                            tool_params["overwrite"] = True
    
                    tool_result = self._execute_tool_action(tool_name, tool_params)
                    result["tool_result"] = tool_result
    
                    # 根据工具执行结果判断是否成功完成
                    if "error" in tool_result:
                        # 检查是否是文件已存在的错误
                        if tool_result.get("error_type") == "file_exists":
                            pass  # 文件已存在的情况暂不处理
                        else:
                            result["success"] = False
                    else:
                        # 工具执行成功，将结果返回给操作agent进行进一步处理
                        logger.info("工具执行成功，将结果返回给操作agent进行进一步处理")
    
                        # 保存当前操作结果，用于构建新的提示词
                        previous_operation = json.dumps(
                            result, ensure_ascii=False, indent=2
                        )
    
                        # 转义花括号，防止被解释为格式化占位符
                        previous_operation = previous_operation.replace(
                            "{", "{{"
                        ).replace("}", "}}")
    
                        # 保存助手消息到操作历史记录
                        operation_history.append({"role": "assistant", "content": response.get("content", "")})
                        
                        # 保存工具结果到操作历史记录
                        operation_history.append(
                            {"role": "tool_result", "content": json.dumps(tool_result, ensure_ascii=False)}
                        )
                        
                        # 保存操作历史记录
                        self._save_operation_history(task_number, operation_history)
    
                        # 重置消息列表
                        self.reset_messages()
    
                        # 添加系统提示 - 只添加一次系统消息
                        system_added = False  # 重置系统消息标志
                        for msg in operation_history:
                            if not isinstance(msg, dict):
                                continue
                                
                            role = msg.get("role", "")
                            content = msg.get("content", "")
                            
                            # 只添加一次系统提示
                            if role == "system":
                                if not system_added:
                                    self.messages.append(msg)
                                    system_added = True
                            # 添加其他消息类型
                            elif role in ["tool_result", "assistant"]:
                                self.messages.append(msg)
    
                        # 构建新的提示词，包含工具执行结果
                        tool_step_prompt = TOOL_STEP_PROMPT.format(
                            refinement_content=refinement_content,
                            planning_content=planning_content,
                            previous_operation=previous_operation,
                            tool_result=json.dumps(
                                tool_result, ensure_ascii=False, indent=2
                            )
                            .replace("{", "{{")
                            .replace("}", "}}"),  # 同样转义工具结果中的花括号
                            WORKSPACE_ABS_PATH=WORKSPACE_ABS_PATH,  # 添加WORKSPACE_ABS_PATH参数
                        )
    
                        # 添加新的提示词
                        self.add_message("user", tool_step_prompt)
    
                        try:
                            # 发送请求
                            logger.info("🔄 正在向LLM发送工具结果处理请求...")
                            tool_response = self.send_to_llm()
    
                            # 解析响应
                            tool_result_handling = self.parse_json_response(
                                tool_response
                            )
    
                            # 确保解析结果是字典
                            if not isinstance(tool_result_handling, dict):
                                logger.error(f"解析工具响应失败: {tool_response}")
                                tool_result_handling = {
                                    "success": True,
                                    "explanation": "任务已完成，但无法解析详细结果。",
                                }
    
                            # 更新结果
                            result.update(tool_result_handling)
    
                            # 默认设置为True，除非明确指定为False
                            result["success"] = tool_result_handling.get(
                                "success", True
                            )
                            
                            # 如果任务成功完成，保存历史记录但不清空
                            if result["success"]:
                                # 保存助手消息到操作历史记录
                                operation_history.append({"role": "assistant", "content": tool_response.get("content", "")})
                                # 保存历史记录
                                self._save_operation_history(task_number, operation_history)
                                logger.debug(f"任务 {task_number} 成功完成，已保存操作历史记录，当前历史记录长度: {len(operation_history)}")
                                # 移除清空操作历史记录的代码
                                # self._clean_operate_history(task_number)  # 注释掉这行
                            else:
                                # 保存助手消息到操作历史记录
                                operation_history.append({"role": "assistant", "content": tool_response.get("content", "")})
                                self._save_operation_history(task_number, operation_history)
                                logger.debug(f"已保存任务 {task_number} 的操作历史记录，当前历史记录长度: {len(operation_history)}")
                            
                        except Exception as e:
                            logger.error(f"处理工具结果时出错: {e}")
                            result["success"] = True  # 默认认为工具执行成功
                            result["explanation"] = (
                                "工具执行成功，但处理结果时出现错误。"
                            )
                            # 保存助手消息到操作历史记录
                            operation_history.append({"role": "assistant", "content": "处理工具结果时出错"})
                            self._save_operation_history(task_number, operation_history)
                            # 移除清空操作历史记录的代码
                            # self._clean_operate_history(task_number)  # 注释掉这行
                else:
                    result["error"] = "未指定工具名称"
                    result["success"] = False

            # 在run方法中添加对search_tool的处理
            elif action_type == "search_tool":
                # 处理工具查询
                tool_name = result.get("use_tool")
                if tool_name:
                    tool_info = self._get_tool_info(tool_name)
                    result["tool_info"] = tool_info
                    
                    # 保存助手消息到操作历史记录
                    operation_history.append({"role": "assistant", "content": response.get("content", "")})
                    
                    # 保存工具信息到操作历史记录
                    operation_history.append(
                        {"role": "tool_result", "content": json.dumps(tool_info, ensure_ascii=False)}
                    )
                    
                    # 保存操作历史记录
                    self._save_operation_history(task_number, operation_history)
                    
                    # 重置消息列表
                    self.reset_messages()
                    
                    # 添加系统提示 - 只添加一次系统消息
                    system_added = False  # 重置系统消息标志
                    for msg in operation_history:
                        if not isinstance(msg, dict):
                            continue
                            
                        role = msg.get("role", "")
                        content = msg.get("content", "")
                        
                        # 只添加一次系统提示
                        if role == "system":
                            if not system_added:
                                self.messages.append(msg)
                                system_added = True
                        # 添加其他消息类型
                        elif role in ["tool_result", "assistant"]:
                            self.messages.append(msg)
                    
                    # 构建新的提示词，包含工具信息
                    search_tool_prompt = SEARCH_TOOL_PROMPT.format(
                        tool_info=json.dumps(tool_info, ensure_ascii=False, indent=2)
                    )
                    self.add_message("user", search_tool_prompt)
                    
                    # 发送请求
                    logger.info(f"🔄 正在向LLM发送工具查询请求: {tool_name}...")
                    response = self.send_to_llm()
                    
                    # 解析响应
                    result = self.parse_json_response(response)
                    result["success"] = False  # 工具查询后需要继续操作

            elif action_type == "history":
                # 处理历史记录请求
                pull_history = result.get("pull_history", "")
                if pull_history:
                    history_result = self._get_operation_history(pull_history)
                    result["history_result"] = history_result
                    
                    # 保存助手消息到操作历史记录
                    operation_history.append({"role": "assistant", "content": response.get("content", "")})
                    
                    # 保存历史记录请求结果到操作历史记录
                    operation_history.append(
                        {"role": "history_result", "content": json.dumps(history_result, ensure_ascii=False)}
                    )
                    
                    # 保存操作历史记录
                    self._save_operation_history(task_number, operation_history)
                    
                    # 重置消息列表
                    self.reset_messages()
                    
                    # 添加系统提示和历史对话
                    system_added = False
                    for msg in operation_history:
                        if not isinstance(msg, dict):
                            continue
                            
                        role = msg.get("role", "")
                        content = msg.get("content", "")
                        
                        if role == "system":
                            if not system_added:
                                self.messages.append(msg)
                                system_added = True
                        elif role in ["tool_result", "assistant", "history_result"]:
                            self.messages.append(msg)
                    
                    # 构建新的提示词，包含历史记录结果
                    history_step_prompt = """您之前请求了历史操作记录，现在历史记录已获取，请根据历史记录继续完成当前任务。

# 历史记录结果
{history_result}

请根据历史记录结果，完成以下工作：
1. 分析历史记录，提取有用信息
2. 继续执行当前TODO项

请记住，所有文件操作必须使用系统提供的工具进行，不要尝试直接操作文件系统。
文件路径应使用绝对路径，默认工作目录为：{WORKSPACE_ABS_PATH}

请以严格JSON格式返回结果。
""".format(
                        history_result=json.dumps(history_result, ensure_ascii=False, indent=2)
                        .replace("{", "{{")
                        .replace("}", "}}"),
                        WORKSPACE_ABS_PATH=WORKSPACE_ABS_PATH,
                    )
                    
                    # 添加新的提示词
                    self.add_message("user", history_step_prompt)
                    
                    try:
                        # 发送请求
                        logger.info("🔄 正在向LLM发送历史记录处理请求...")
                        history_response = self.send_to_llm()
                        
                        # 解析响应
                        history_result_handling = self.parse_json_response(history_response)
                        
                        # 确保解析结果是字典
                        if not isinstance(history_result_handling, dict):
                            logger.error(f"解析历史记录响应失败: {history_response}")
                            history_result_handling = {
                                "success": True,
                                "explanation": "历史记录已获取，但无法解析详细结果。",
                            }
                        
                        # 更新结果
                        result.update(history_result_handling)
                        
                        # 默认设置为True，除非明确指定为False
                        result["success"] = history_result_handling.get("success", True)
                        
                        # 保存助手消息到操作历史记录
                        operation_history.append({"role": "assistant", "content": history_response.get("content", "")})
                        self._save_operation_history(task_number, operation_history)
                        
                    except Exception as e:
                        logger.error(f"处理历史记录结果时出错: {e}")
                        result["success"] = True
                        result["explanation"] = "历史记录获取成功，但处理结果时出现错误。"
                        operation_history.append({"role": "assistant", "content": "处理历史记录结果时出错"})
                        self._save_operation_history(task_number, operation_history)
                    else:
                        result["error"] = "未指定要获取的历史记录"
                        result["success"] = False

            else:  # action_type == "none" 或其他情况
                # 无需执行任何操作，直接返回结果
                # 默认设置为True，除非明确指定为False
                result["success"] = result.get("success", True)
                # 如果任务成功完成，保存历史记录但不清空
                if result["success"]:
                    # 保存助手消息到操作历史记录
                    operation_history.append({"role": "assistant", "content": response.get("content", "")})
                    self._save_operation_history(task_number, operation_history)
                    logger.debug(f"任务 {task_number} 成功完成，已保存操作历史记录，当前历史记录长度: {len(operation_history)}")
                    # 移除清空操作历史记录的代码
                    # self._clean_operate_history(task_number)  # 注释掉这行
                else:
                    # 保存助手消息到操作历史记录
                    operation_history.append({"role": "assistant", "content": response.get("content", "")})
                    self._save_operation_history(task_number, operation_history)
                    logger.debug(f"任务 {task_number} 未成功完成，已保存操作历史记录，当前历史记录长度: {len(operation_history)}")

            return result
        except Exception as e:
            logger.error(f"操作Agent执行失败: {e}")
            import traceback

            logger.debug(f"操作Agent执行异常堆栈: {traceback.format_exc()}")
            return {"error": f"操作Agent执行失败: {str(e)}", "success": False}

    def _get_history_file_path(self, task_number):
        """获取历史记录文件路径"""
        # 确保task_number是有效的格式
        if not isinstance(task_number, str):
            task_number = str(task_number)
        
        # 将任务编号格式化为文件名，例如：1.1 -> 1_1.json
        file_name = f"{task_number.replace('.', '_')}.json"
        if not file_name.endswith('.json'):
            file_name += '.json'
            
        return os.path.join(self.operation_history_dir, file_name)
    
    def _read_operation_history(self, task_number):
        """读取操作历史记录"""
        try:
            history_file = self._get_history_file_path(task_number)
            logger.debug(f"尝试读取任务 {task_number} 的操作历史记录: {history_file}")
            
            if not os.path.exists(history_file):
                logger.debug(f"历史记录文件不存在: {history_file}，返回空列表")
                return []
                
            with open(history_file, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    logger.debug(f"历史记录文件为空: {history_file}，返回空列表")
                    return []
                history = json.loads(content)
                logger.debug(f"成功读取任务 {task_number} 的操作历史记录，包含 {len(history)} 条记录")
                return history
        except Exception as e:
            logger.error(f"读取操作历史记录失败: {e}")
            import traceback
            logger.debug(f"读取操作历史记录异常堆栈: {traceback.format_exc()}")
            return []
            
    def _save_operation_history(self, task_number, history):
        """保存操作历史记录"""
        try:
            history_file = self._get_history_file_path(task_number)
            logger.debug(f"尝试保存任务 {task_number} 的操作历史记录: {history_file}，共 {len(history)} 条记录")
            
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            logger.debug(f"保存操作历史记录成功: {history_file}")
        except Exception as e:
            logger.error(f"保存操作历史记录失败: {e}")

    def _get_operation_history(self, history_ids):
        """获取指定的操作历史记录
        
        Args:
            history_ids: 历史记录ID，格式为"1.1, 1.2, 1.3"
        
        Returns:
            历史记录内容的字典，键为历史记录ID，值为历史记录内容
        """
        try:
            # 解析历史记录ID
            history_id_list = [id.strip() for id in history_ids.split(",") if id.strip()]
            logger.debug(f"尝试获取历史记录: {history_id_list}")
            
            history_results = {}
            
            for history_id in history_id_list:
                # 获取历史记录文件路径
                history_file = self._get_history_file_path(history_id)
                
                if not os.path.exists(history_file):
                    logger.warning(f"历史记录文件不存在: {history_file}")
                    history_results[history_id] = {"error": "历史记录不存在"}
                    continue
                    
                # 读取历史记录文件内容
                with open(history_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if not content.strip():
                        logger.warning(f"历史记录文件为空: {history_file}")
                        history_results[history_id] = {"error": "历史记录为空"}
                        continue
                    
                    # 解析历史记录内容
                    history_data = json.loads(content)
                    
                    # 提取所有相关消息内容，包括助手消息和工具结果
                    processed_history = []
                    for msg in history_data:
                        if isinstance(msg, dict):
                            role = msg.get("role", "")
                            content = msg.get("content", "")
                            
                            # 处理助手消息
                            if role == "assistant":
                                try:
                                    # 移除可能的Markdown代码块标记
                                    cleaned_content = content.replace("```json", "").replace("```", "").strip()
                                    # 解析JSON内容
                                    json_content = json.loads(cleaned_content)
                                    processed_history.append(json_content)
                                except json.JSONDecodeError:
                                    # 如果不是有效的JSON，则保留原始内容
                                    processed_history.append({"raw_content": content})
                            
                            # 处理工具结果消息
                            elif role == "tool_result":
                                try:
                                    # 解析工具结果
                                    tool_result = json.loads(content)
                                    processed_history.append({
                                        "type": "tool_result",
                                        "result": tool_result
                                    })
                                except json.JSONDecodeError:
                                    processed_history.append({
                                        "type": "tool_result",
                                        "raw_content": content
                                    })
                
                history_results[history_id] = processed_history
            
            logger.info(f"成功获取历史记录: {list(history_results.keys())}")
            return history_results
            
        except Exception as e:
            logger.error(f"获取操作历史记录失败: {e}")
            import traceback
            logger.debug(f"获取操作历史记录异常堆栈: {traceback.format_exc()}")
            return {"error": f"获取操作历史记录失败: {str(e)}"}

    def _get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """获取指定工具的详细信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具详细信息
        """
        try:
            tools_config = get_tools_config()
            for tool in tools_config:
                if tool.get("name") == tool_name:
                    return {
                        "status": "success",
                        "tool_info": json.dumps(tool, ensure_ascii=False, indent=2)
                    }
            return {
                "status": "error",
                "message": f"未找到工具: {tool_name}"
            }
        except Exception as e:
            logger.error(f"获取工具信息失败: {e}")
            return {
                "status": "error",
                "message": f"获取工具信息失败: {str(e)}"
            }
