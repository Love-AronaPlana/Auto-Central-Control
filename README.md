# 🚀 Auto-Central-Control (ACC)
基于LLM的自动化中央控制系统，支持需求解析、任务分解、自动化执行和操作总结


## 📝 简介
为中国宝宝量身打造的全中文类Manus，一键部署，方便运行

灵感来源于[Manus](https://manus.im/)


## 🎯 核心功能
| 模块                | 说明                                                                 | 文件路径                          |
|---------------------|----------------------------------------------------------------------|-----------------------------------|
| **智能工作流引擎**  | 多步骤任务分解与自动化执行                                            | `ACC/workflow.py`                 |
| **Agent系统**       | - 细化Agent：需求拆解<br>- 操作Agent：工具调用<br>- 总结Agent：报告生成 | `ACC/agent/refinement.py`<br>`ACC/agent/operate.py`<br>`ACC/agent/sumup.py` |
| **工具集成**        | - 文件读写<br>- Python解释器<br>- 支持自定义扩展                       | `ACC/tool/read_file.py`<br>`ACC/tool/python_interpreter.py` |
| **记忆系统**        | - 操作历史记录<br>- 执行总结报告                                      | `ACC/memory/operation_generalization/`<br>`ACC/memory/summary.md` |


## 🚀 快速开始
### 1. 克隆与安装
```bash
git clone https://github.com/your-org/Auto-Central-Control.git
cd Auto-Central-Control
pip install -r requirements.txt
```

### 2. 配置LLM参数
在 `ACC/config/config.json` 中配置：
```json
{
  "api_key": "your-openai-key",
  "model": "gpt-4",
  "base_url": "https://api.openai.com/v1"
}
```

### 3. 运行示例
```bash
python start.py
```


## 🌳 项目结构
```
Auto-Central-Control/
├── ACC/
│   ├── agent/        # 智能体模块
│   ├── tool/         # 工具集合
│   ├── memory/       # 记忆系统
│   ├── workflow.py   # 工作流引擎
│   └── config.py     # 配置管理
└── start.py           # 主入口
```


## 🛠️ 扩展开发
### 添加新工具
```python
from ACC.tool.base import BaseTool, ToolRegistry

class NewTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="new_tool",
            description="工具描述"
        )

    def execute(self, params):
        # 实现工具逻辑
        return {"status": "success"}

ToolRegistry.register(NewTool())
```

### 自定义工作流
```python
from ACC.workflow import Workflow

class CustomWorkflow(Workflow):
    def execute(self, user_input):
        # 实现自定义流程
        return super().execute(user_input)
```


## 📚 文档
- **操作手册**：[查看文档](https://your-docs-url.com)
- **更新日志**：[CHANGELOG.md](https://github.com/your-org/Auto-Central-Control/blob/main/CHANGELOG.md)
