#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
启动脚本 - 正常模式
不开启debug模式启动Auto-Central-Control
"""

import sys
from start import main

if __name__ == "__main__":
    main(debug=False)