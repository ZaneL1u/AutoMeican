#!/bin/bash

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p ~/.meican/logs

echo "启动 Docker Compose..."
docker-compose up -d

echo "容器启动完成！"
echo "访问地址: http://localhost:8000"
echo "数据目录: ~/.meican/"
echo "日志目录: ~/.meican/logs/"
