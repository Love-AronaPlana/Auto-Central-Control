# 系统常量定义

# 文件路径常量
import os
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 各模块目录
PROMPTS_DIR = ROOT_DIR / 'prompts'
CONFIG_DIR = ROOT_DIR / 'config'
WORKSPACE_DIR = ROOT_DIR / 'workspace'
MEMORY_DIR = ROOT_DIR / 'memory'
WORKFLOW_DIR = ROOT_DIR / 'workflow'
TOOLS_DIR = ROOT_DIR / 'tools'
LOG_DIR = ROOT_DIR / 'log'

# 角色定义
SYSTEM_ROLE = "system"
USER_ROLE = "user"
ASSISTANT_ROLE = "assistant"

# 工作流状态
STATUS_IDLE = "idle"
STATUS_ANALYZING = "analyzing"
STATUS_SELECTING_TOOL = "selecting_tool"
STATUS_EXECUTING = "executing"
STATUS_PROCESSING_RESULT = "processing_result"
STATUS_COMPLETED = "completed"

# 工具名称
TOOL_FILE_READ = "file_read"
TOOL_FILE_WRITE = "file_write"