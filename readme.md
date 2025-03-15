# Auto-Central-Control 自动化中央控制系统


## 项目概述

基于多Agent协作的自动化任务处理系统，能够智能分解用户需求、执行操作并自动修复错误。系统包含完整的自动化工作流程：

🔧 核心功能：
- **智能任务分解**：将用户需求拆解为可执行步骤
- **多Agent协作**：执行/分析/复查/修复/总结Agent协同工作
- **插件系统**：支持文件管理、文本分析等扩展功能
- **自动错误修复**：3次自动修复尝试机制
- **系统自检**：启动时自动检查组件状态
- **详细日志**：完整记录执行过程

## 快速开始

### 环境要求
- Python 3.8+
- pip包管理工具

### 安装步骤
```bash
# 克隆仓库
git clone https://github.com/Love-AronaPlana/Auto-Central-Control.git

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制模板文件）
cp .env.example .env
