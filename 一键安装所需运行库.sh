#!/bin/bash

# 创建pip配置目录
mkdir -p ~/.pip 2>/dev/null

# 创建并写入pip配置文件
cat << EOF > ~/.pip/pip.conf
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
EOF

# 安装依赖
pip install -r requirements.txt    