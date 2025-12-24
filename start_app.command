#!/bin/bash

# 1. 切换到项目文件夹 (根据你之前的路径)
cd ~/Documents/Confuser_MVP

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 启动 Streamlit
echo "正在启动 Confuser 系统..."
python -m streamlit run app.py
