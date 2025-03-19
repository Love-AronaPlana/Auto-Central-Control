"""内存管理模块，负责管理ASN的内存

该模块提供了内存管理功能，包括保存和读取AI生成的文件、记录运行状态等。
所有需要持久化存储的数据都应通过该模块进行管理。
"""

import json
import logging
import os
import shutil  # 添加缺失的shutil模块导入
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# 内存目录路径
MEMORY_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),  # 直接指向ASN/memory目录
)

# 确保内存目录存在
if not os.path.exists(MEMORY_DIR):
    os.makedirs(MEMORY_DIR)
    logger.info(f"创建内存目录: {MEMORY_DIR}")


class MemoryManager:
    """内存管理器，负责管理ASN的内存"""

    @staticmethod
    def save_file(filename: str, content: str) -> str:
        """保存文件到内存目录

        Args:
            filename: 文件名
            content: 文件内容

        Returns:
            文件完整路径
        """
        file_path = os.path.join(MEMORY_DIR, filename)

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"保存文件成功: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            raise

    @staticmethod
    def read_file(filename: str) -> str:
        """从内存目录读取文件

        Args:
            filename: 文件名

        Returns:
            文件内容
        """
        file_path = os.path.join(MEMORY_DIR, filename)

        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                raise FileNotFoundError(f"文件不存在: {file_path}")

            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            logger.info(f"读取文件成功: {file_path}")
            return content
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            raise

    @staticmethod
    def save_json(filename: str, data: Dict[str, Any]) -> str:
        """保存JSON数据到内存目录

        Args:
            filename: 文件名
            data: JSON数据

        Returns:
            文件完整路径
        """
        # 确保文件名以.json结尾
        if not filename.endswith(".json"):
            filename += ".json"

        content = json.dumps(data, ensure_ascii=False, indent=2)
        return MemoryManager.save_file(filename, content)

    @staticmethod
    def read_json(filename: str) -> Dict[str, Any]:
        """从内存目录读取JSON数据

        Args:
            filename: 文件名

        Returns:
            JSON数据
        """
        # 确保文件名以.json结尾
        if not filename.endswith(".json"):
            filename += ".json"

        content = MemoryManager.read_file(filename)
        return json.loads(content)

    @staticmethod
    def save_todo(todo_list: List[Dict[str, Any]]) -> str:
        """保存TODO列表到内存目录

        Args:
            todo_list: TODO列表

        Returns:
            文件完整路径
        """
        # 生成TODO文件名，格式为todo_YYYYMMDD.md
        today = datetime.now().strftime("%Y%m%d")
        filename = f"todo_{today}.md"

        # 生成TODO内容
        content = "# TODO List\n\n"
        for i, todo in enumerate(todo_list, 1):
            content += f"## {i}. {todo.get('title', '未命名任务')}\n\n"
            content += f"- 描述: {todo.get('description', '无描述')}\n"
            content += f"- 状态: {todo.get('status', '待处理')}\n"
            content += f"- 优先级: {todo.get('priority', '中')}\n"
            content += "\n"

        return MemoryManager.save_file(filename, content)

    @staticmethod
    def list_files() -> List[str]:
        """列出内存目录中的所有文件

        Returns:
            文件名列表
        """
        try:
            if not os.path.exists(MEMORY_DIR):
                return []

            files = []
            for root, _, filenames in os.walk(MEMORY_DIR):
                for filename in filenames:
                    rel_path = os.path.relpath(os.path.join(root, filename), MEMORY_DIR)
                    files.append(rel_path)

            return files
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            raise

    @staticmethod
    # 修改保存路径处理逻辑
    @staticmethod
    def clean_todo_directory():
        """清空ASN模块的todo目录"""
        todo_dir = os.path.join(MEMORY_DIR, "todo")
        if os.path.exists(todo_dir):
            for filename in os.listdir(todo_dir):
                file_path = os.path.join(todo_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logger.error(f"删除文件失败 {file_path}: {e}")
            logger.info(f"已清空TODO目录: {todo_dir}")

    @staticmethod
    def clean_refinement_directory():
        """清空细化目录"""
        refinement_dir = os.path.join(MEMORY_DIR, "todo", "refinement")
        if os.path.exists(refinement_dir):
            shutil.rmtree(refinement_dir)
        os.makedirs(refinement_dir, exist_ok=True)


# 创建全局内存管理器实例
_memory_manager = None


def get_memory_manager() -> MemoryManager:
    """获取内存管理器实例

    Returns:
        内存管理器实例
    """
    global _memory_manager

    if _memory_manager is None:
        _memory_manager = MemoryManager()

    return _memory_manager
