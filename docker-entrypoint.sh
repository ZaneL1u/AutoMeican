#!/bin/bash
set -e

# 创建必要的目录
mkdir -p /app/data/logs
python manage.py collectstatic --noinput || true
python manage.py migrate
crond
python manage.py crontab add
exec python manage.py runserver 0.0.0.0:8000