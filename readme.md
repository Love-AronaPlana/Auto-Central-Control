# Auto - Central - Control 自动化中央控制系统



![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 项目概述

基于多 Agent 协作的自动化任务处理系统，能够智能分解用户需求、执行操作并自动修复错误。系统采用模块化设计，包含完整的自动化工作流和错误恢复机制。



![系统架构图](docs/images/architecture.png)

## 核心功能

### 🧠智能任务处理

**需求分解**：通过 StepAgent 将复杂需求拆解为可执行步骤。

**动态分析**：AnalysisAgent 生成详细执行计划。

**多级验证**：ReviewAgent + FixAgent 实现执行结果校验与自动修复。

**智能总结**：SummaryAgent 生成执行报告。

### ⚙️系统特性

**插件体系**：支持文件管理、文本分析等扩展功能。

**错误自愈**：3 层自动修复机制（错误重试 / 方案替换 / 降级处理）。

**状态监控**：实时记录执行过程，支持执行轨迹回溯。

**环境隔离**：独立内存管理模块，支持多会话隔离。

## 快速开始

### 环境要求

**Python 版本**：需 Python 3.8 及以上版本。

**pip 版本**：pip 21.0 及以上版本。

**虚拟环境**：强烈推荐使用虚拟环境来管理项目依赖，以避免不同项目间的依赖冲突。例如，可以使用`venv`模块创建虚拟环境：



```
python -m venv myenv

source myenv/bin/activate  # 在Windows上使用 \`myenv\Scripts\activate\`
```

### 安装步骤



```
# 克隆仓库

git clone https://github.com/Love-AronaPlana/Auto-Central-Control.git

cd Auto-Central-Control

# 安装依赖

pip install -r requirements.txt

# 配置环境（复制模板文件）

cp.env.example.env
```

### 配置文件说明

编辑`.env`文件：



```
# OpenAI API配置

API_URL=https://gemini-api-gavinchen.deno.dev/v1

API_KEY=your_api_key_here

MODEL_NAME=gemini-2.0-flash

# 系统参数

DEBUG=false

CLEAN_LOG_ON_START=true

MEMORY_RETENTION_COUNT=5
```

### 使用指南

启动系统：



```
python start.py
```

### 示例任务



```
请帮我完成以下操作：

1\. 分析workspace目录下的所有文本文件

2\. 统计高频词汇

3\. 生成分析报告
```

## 项目结构



```
Auto-Central-Control/

├── agent/               # Agent核心模块

│   ├── analysis_agent.py  # 负责动态分析任务的代码文件

│   ├── fix_agent.py       # 处理错误修复相关的代码文件

│   └──...                # 其他与Agent相关的代码文件

├── workflow/            # 工作流引擎，包含定义和执行自动化工作流的代码

├── memory/              # 会话记忆管理，用于存储和管理执行过程中的相关数据

├── plugins/             # 插件系统，可在此目录下添加新插件以扩展系统功能

├── config.py            # 配置加载器，负责读取和解析项目的配置文件

├── start.py             # 系统入口，启动整个自动化中央控制系统

└── requirements.txt     # 项目依赖文件，记录了项目运行所需的Python包及其版本
```

## 开发文档

### 扩展插件

在`plugins`目录中创建新插件类，并实现标准接口：



```
class BasePlugin:

   def execute(self, operation: dict) -> dict:

       # 在此处实现具体功能逻辑

       # operation参数是一个字典，包含插件执行所需的输入信息

       # 返回值是一个字典，包含插件执行的结果

       result = {}

       # 示例：假设operation包含一个文件路径，读取文件内容并返回长度

       file_path = operation.get('file_path')

       if file_path:

           with open(file_path, 'r') as f:

               content = f.read()

               result\['content_length'] = len(content)

       return result
```

### 调试模式

设置`DEBUG=true`时，系统将：

**记录详细通信日志**：详细记录系统内部各个组件之间的通信信息，便于排查问题。

**保留中间过程数据**：保留任务执行过程中的中间数据，有助于分析任务执行流程和定位错误。

**启用开发人员控制台**：提供一个交互式控制台，开发人员可以在其中执行命令、查看变量值等，方便调试。

### 贡献指南

欢迎提交 PR，请遵循以下规范：

**新功能开发**：新功能开发需包含单元测试，以确保功能的正确性和稳定性。

**修改核心逻辑**：修改核心逻辑需更新对应文档，保证文档与代码的一致性。

**插件开发**：插件开发请提供使用示例，方便其他开发者理解和使用插件。

## 许可证

本项目采用 MIT License。MIT 许可证是一种宽松的开源许可证，允许他人自由使用、修改和分发本项目代码，只要保留原作者的版权声明和许可证文件即可。具体许可证文本请查看项目根目录下的`LICENSE`文件。
