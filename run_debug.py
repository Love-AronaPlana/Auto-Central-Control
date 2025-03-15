#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
run_debug.py - 启动脚本（开启debug模式）

该脚本用于启动Auto-Central-Control系统，开启debug模式。
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置DEBUG环境变量为True
os.environ["DEBUG"] = "true"

# 导入并运行start.py
from start import main

if __name__ == "__main__":
    main()
