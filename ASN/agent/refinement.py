from typing import Dict, Any
import logging
import json
import re  # 添加缺失的re模块导入
from pathlib import Path
from ASN.agent.base import BaseAgent
from ASN.memory.memory_manager import MemoryManager
from ASN.prompt.refinement import SYSTEM_PROMPT, FIRST_STEP_PROMPT  # 添加缺失的导入

logger = logging.getLogger(__name__)


# 在类中添加计数器并修改保存路径
class RefinementAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Refinement Agent", system_prompt=SYSTEM_PROMPT  # 使用正确导入的常量
        )
        self.task_counter = 1  # 新增任务计数器

    def run(self) -> Dict[str, Any]:
        """运行细化流程"""
        # 添加读取TODO文件的代码
        current_dir = Path(__file__).parent
        todo_path = current_dir.parent / "memory" / "todo" / "planning.md"
        todos_content = todo_path.read_text(encoding="utf-8")  # 定义todos_content

        self.add_message("user", FIRST_STEP_PROMPT.format(current_todos=todos_content))
        # 获取LLM响应
        logger.info("🔄 正在生成细化步骤...")
        response = self.send_to_llm()
        refinement_data = self.parse_json_response(response)

        # 保存细化结果
        if "current_task" in refinement_data:
            # 加强正则匹配，只匹配开头的数字编号
            task_number = re.search(r"^(\d+\.\d+)", refinement_data["current_task"])
            if task_number:
                # 替换点为下划线并截断后续内容
                filename = f"{task_number.group().replace('.', '_')}.md"
            else:
                filename = "unknown_task.md"
                logger.warning(f"未找到有效任务编号: {refinement_data['current_task']}")

            # 新保存路径
            save_path = f"todo/refinement/{filename}"
            MemoryManager.save_file(save_path, self._generate_md(refinement_data))

        return refinement_data

    def _find_first_unchecked(self, content: str) -> str:  # 移动到类内部
        """查找第一个未完成的任务项"""
        lines = content.split("\n")
        for line in lines:
            if line.strip().startswith("- [ ]"):
                return line.strip()
        return ""

    def _generate_md(self, data: Dict) -> str:
        """生成Markdown格式的细化文档"""
        md_content = f"# {data['current_task']}\n\n{data['task_description']}\n\n"

        for task in data["sub_tasks"]:
            md_content += f"## 步骤 {task['step']}: {task['action']}\n"
            md_content += "- 注意事项:\n"
            for note in task["notes"]:
                md_content += f"  - {note}\n"
            md_content += "- 风险点:\n"
            for risk in task["risks"]:
                md_content += f"  - {risk}\n"
            md_content += "\n"

        return md_content

    def parse_json_response(self, response: Dict) -> Dict:
        """专用JSON解析方法"""
        content = response.get("content", "").replace("\\n", "\n")

        try:
            # 去除可能的代码块标记
            content = content.split("```json")[-1].split("```")[0].strip()
            return json.loads(content)
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"JSON解析失败: {str(e)}")
            logger.debug(f"原始响应内容: {content[:500]}")  # 记录前500字符
            return {"error": f"JSON解析失败: {str(e)}"}
