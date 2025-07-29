#!/bin/bash

# AutoMeican Docker 构建和运行脚本

set -e

echo "=== AutoMeican Docker 构建和运行 ==="

# 检查是否存在 .env 文件
if [ ! -f .env ]; then
    echo "创建 .env 文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件，设置 MEICAN_GLOBAL_PASSWORD 为你的实际密码"
    echo "   然后重新运行此脚本"
    exit 1
fi

# 读取 .env 文件
source .env

# 检查密码是否已设置
if [ "$MEICAN_GLOBAL_PASSWORD" = "your_actual_password_here" ]; then
    echo "❌ 请在 .env 文件中设置正确的 MEICAN_GLOBAL_PASSWORD"
    exit 1
fi

echo "✅ 环境配置检查通过"

# 停止现有容器
echo "停止现有容器..."
docker-compose down || true

# 构建镜像
echo "构建 Docker 镜像..."
docker-compose build --no-cache

# 启动服务
echo "启动服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查 CSRF 配置
echo "检查 CSRF 配置..."
docker-compose exec app python manage.py check_csrf || echo "CSRF 检查失败，但服务可能仍然正常"

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

# 显示日志
echo "显示最近的日志..."
docker-compose logs --tail=20

echo ""
echo "🎉 AutoMeican 服务已启动！"
echo "访问地址: http://localhost:8000"
echo "如果遇到 CSRF 错误，请查看上面的配置检查结果"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  进入容器: docker-compose exec app bash"
echo "  检查 CSRF: docker-compose exec app python manage.py check_csrf"
echo ""
