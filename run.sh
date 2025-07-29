#!/bin/bash

# AutoMeican 启动脚本（非 Docker 版本）

set -e

echo "=== AutoMeican 启动脚本 ==="

# 检查 Python 虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt || {
    echo "生成 requirements.txt..."
    pipenv requirements > requirements.txt
    pip install -r requirements.txt
}

# 安装额外依赖
pip install pytz requests django-crontab

# 运行数据库迁移
echo "运行数据库迁移..."
python manage.py migrate

# 设置环境变量
export DJANGO_SETTINGS_MODULE=AutoMeican.settings
export MEICAN_GLOBAL_PASSWORD=${MEICAN_GLOBAL_PASSWORD:-"MeicanAuto0rder"}

# 安装 crontab 任务
echo "安装定时任务..."
python manage.py crontab add || echo "定时任务安装失败，请手动执行"

# 启动服务
echo "启动 Django 服务..."
echo "访问地址: http://127.0.0.1:8000"
echo "按 Ctrl+C 停止服务"
python manage.py runserver
