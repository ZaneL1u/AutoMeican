#!/bin/bash
set -e

# 创建必要的目录
mkdir -p /app/data/logs
python manage.py migrate

# 添加 cron 任务
echo "Adding cron jobs..."
python manage.py crontab add

# 检查当前 crontab
echo "Current crontab:"
crontab -l

# 启动 cron 服务并记录日志
echo "Starting crond..."
crond

exec python manage.py runserver 0.0.0.0:8000