# AutoMeican - 美餐自动点餐系统

🍽️ 一个基于 Django 的美餐自动点餐系统，帮助你告别手动点餐的烦恼！

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/django-5.2%2B-green.svg)](https://djangoproject.com)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://docker.com)

## 🎯 为什么创建这个项目

在日常工作中，我们经常面临这样的困扰：

- 🕘 **忘记点餐**：工作繁忙时经常忘记在指定时间内点餐，错过用餐时间
- 🔄 **重复操作**：每天都要重复登录美餐、浏览菜单、选择菜品的繁琐操作
- 🎲 **选择困难**：面对众多菜品时不知道选什么，浪费大量时间纠结
- 👥 **团队管理**：公司多个同事都需要点餐，逐一提醒和管理很麻烦
- ⏰ **时间限制**：美餐的点餐时间窗口有限，一旦错过就只能饿肚子

**AutoMeican** 就是为了解决这些痛点而诞生的！它能够：
- ✅ 自动在指定时间为你点餐，再也不用担心忘记
- ✅ 智能选择菜品，优先选择营养丰富的自助餐
- ✅ 支持多用户管理，一套系统搞定全团队的用餐问题
- ✅ 提供简洁的 Web 界面，方便查看和管理
- ✅ 详细的日志记录，让你了解每次点餐的结果

## ✨ 功能特色

- 🔐 **多用户管理**：支持多个美餐账户的统一管理，适合团队使用
- ⏰ **灵活定时调度**：支持多个时间点的定时任务，确保不错过任何可用的自助餐
- 🎯 **智能自助餐点餐**：每次执行时自动检查并点所有可用的"自助"菜品
- 📊 **订单状态追踪**：实时显示今日和明日的订餐状态
- 🐳 **Docker 一键部署**：开箱即用，无需复杂配置
- 📱 **美观 Web 界面**：简洁直观的用户管理界面
- 📋 **完整日志记录**：详细记录每次操作，便于问题排查
- 🔧 **灵活配置**：支持自定义多个定时时间、点餐逻辑等
- 🍽️ **避免重复点餐**：智能检测已点餐品，避免重复下单

## 🚀 快速开始

### 前置准备

在开始使用之前，请确保你已经：

1. **拥有美餐账户**：需要有效的美餐邮箱账户和密码
2. **安装 Docker**（推荐方式）：
   - [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
   - [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
   - [Docker Engine for Linux](https://docs.docker.com/engine/install/)
3. **或者安装 Python 3.13+**（传统方式）

### 方式一：使用 Docker（推荐）

Docker 方式最简单，无需安装 Python 环境，一键即可运行：

1. **克隆项目**
   ```bash
   git clone https://github.com/ZaneL1u/AutoMeican.git
   cd AutoMeican
   ```

2. **设置环境变量（重要）**
   
   创建 `.env` 文件或直接设置环境变量：
   ```bash
   # 方式一：创建 .env 文件
   echo "MEICAN_GLOBAL_PASSWORD=你的美餐密码" > .env
   echo "DJANGO_SECRET_KEY=your-secret-key-here" >> .env
   # 设置多个定时任务时间（推荐用于自助餐）
   echo "CRON_SCHEDULES=0 9 * * *;0 17 * * *;0 11 * * *" >> .env
   
   # 方式二：直接设置环境变量
   export MEICAN_GLOBAL_PASSWORD="你的美餐密码"
   export DJANGO_SECRET_KEY="your-secret-key-here"
   # 多个时间点确保不错过自助餐
   export CRON_SCHEDULES="0 8 * * *;0 9 * * *;0 11 * * *;0 17 * * *;0 18 * * *"
   ```

3. **一键启动**
   ```bash
   # 使用提供的启动脚本（推荐）
   chmod +x start-docker.sh
   ./start-docker.sh
   
   # 或手动启动
   mkdir -p ~/.meican/logs
   docker-compose up -d
   ```

4. **访问系统**
   
   在浏览器中打开：http://localhost:8000

5. **查看运行状态**
   ```bash
   # 查看容器状态
   docker-compose ps
   
   # 查看日志
   docker-compose logs -f
   ```

### 方式二：传统方式部署

如果你偏好传统的 Python 环境部署：

1. **环境要求**
   - Python 3.13+
   - pip 或 pipenv

2. **克隆项目**
   ```bash
   git clone https://github.com/ZaneL1u/AutoMeican.git
   cd AutoMeican
   ```

3. **安装依赖**
   ```bash
   # 使用 pipenv（推荐）
   pip install pipenv
   pipenv install
   pipenv shell
   
   # 或使用 pip
   pip install -r requirements.txt
   ```

4. **设置环境变量**
   ```bash
   export MEICAN_GLOBAL_PASSWORD="你的美餐密码"
   export DJANGO_SECRET_KEY="your-secret-key-here"
   ```

5. **初始化数据库**
   ```bash
   python manage.py migrate
   ```

6. **启动服务**
   ```bash
   # 启动 Web 服务
   python manage.py runserver 0.0.0.0:8000
   
   # 启动定时任务（新开一个终端）
   python manage.py crontab add
   python manage.py crontab show
   ```

## 📱 使用指南

### 第一步：添加用户

1. **访问管理界面**
   
   在浏览器中打开：http://localhost:8000

2. **添加新用户**
   - 在"添加新用户"表单中输入你的美餐邮箱地址
   - 点击"创建用户"按钮
   - 系统会自动验证美餐账户的有效性
   - 验证成功后，用户会被添加到系统中并开启自动点餐


### 第二步：查看订餐状态

用户管理界面会实时显示：

- **用户邮箱**：显示美餐账户邮箱
- **今日状态**：今天的订餐情况（✅已点餐 / ❌未点餐）
- **明日状态**：明天的订餐情况（✅已点餐 / ❌未点餐）
- **菜品名称**：已点餐品的具体名称
- **点餐时间**：具体的下单时间
- **用户状态**：是否启用自动点餐功能

### 第三步：享受自动点餐

系统会在每个指定的时间点自动为所有用户点餐：

1. **自动登录**：使用保存的邮箱和全局密码登录美餐
2. **获取菜单**：获取当天和明天的可用菜单
3. **智能点餐**：
   - 🥗 **优先自助餐**：查找所有包含"自助"关键词的菜品并全部点餐
   - 🔄 **避免重复**：已点过的菜品不会重复点餐
   - 🎲 **备选方案**：如果没有自助餐，则随机选择其他可用菜品
   - 📅 **今明两天**：同时处理今天和明天的可用菜单
4. **下单确认**：自动完成所有可用自助餐的下单流程
5. **记录结果**：将点餐结果保存到数据库和日志文件

### 手动触发点餐

除了自动定时点餐，你也可以手动触发点餐：

```bash
# 为所有用户执行自动点餐
docker exec -it auto-meican-app python manage.py auto_order

# 为指定用户点餐
docker exec -it auto-meican-app python manage.py auto_order --user user@example.com

# 为指定用户在指定日期点餐
docker exec -it auto-meican-app python manage.py auto_order --user user@example.com --date 2024-07-30
```

### 用户管理操作

- **启用/禁用用户**：可以通过数据库或管理界面控制用户的自动点餐功能
- **删除用户**：删除不再需要的用户账户
- **查看历史**：查看用户的历史点餐记录

## ⚙️ 配置说明

### 环境变量配置

| 变量名 | 默认值 | 说明 | 是否必需 |
|--------|--------|------|----------|
| `MEICAN_GLOBAL_PASSWORD` | 无 | 美餐全局密码，用于所有用户的登录验证 | ✅ 必需 |
| `DJANGO_SECRET_KEY` | 自动生成 | Django 密钥，生产环境建议自定义 | 建议设置 |
| `DJANGO_DEBUG` | `True` | 调试模式开关，生产环境建议设置为 False | 可选 |
| `CRON_SCHEDULES` | `0 9 * * *;0 17 * * *` | 多个定时任务时间（用分号分隔） | 可选 |
| `CRON_MORNING_TIME` | `0 9 * * *` | 早餐自动点餐时间（向后兼容） | 可选 |
| `CRON_EVENING_TIME` | `0 17 * * *` | 晚餐自动点餐时间（向后兼容） | 可选 |

### 目录结构说明

```
~/.meican/                     # 数据持久化目录
├── db.sqlite3                # 主数据库文件
└── logs/                     # 日志文件目录
    ├── meican_orders.log     # 点餐操作日志
    └── meican_cron.log       # 定时任务日志
```

### 定时任务配置

系统默认配置了两个定时任务，但支持配置多个时间点：

- **上午9点**：`0 9 * * *` - 检查并点所有可用的自助餐
- **下午5点**：`0 17 * * *` - 再次检查并点餐

**推荐配置（适用于自助餐）：**

自助餐通常全天可订，建议设置多个时间点以确保不错过：

```bash
# 在 .env 文件中设置多个检查时间
CRON_SCHEDULES=0 8 * * *;0 9 * * *;0 11 * * *;0 14 * * *;0 17 * * *;0 18 * * *
```

或在 `docker-compose.yml` 中设置：
```yaml
environment:
  - CRON_SCHEDULES=0 8 * * *;0 9 * * *;0 11 * * *;0 17 * * *
```

**Cron 表达式格式说明：**
```
分钟 小时 日期 月份 星期
 ↓    ↓    ↓    ↓    ↓
 0    9    *    *    *
```

**常用自助餐配置示例：**
- `0 8 * * *;0 17 * * *` - 每天上午8点和下午5点
- `*/30 9-18 * * 1-5` - 工作日9-18点每30分钟检查一次
- `0 9,11,14,17 * * *` - 每天9点、11点、14点、17点
- `0 8 * * *;0 9 * * *;0 11 * * *;0 17 * * *;0 18 * * *` - 密集检查（推荐）

**向后兼容配置：**
```bash
# 仍然支持原有的单独配置方式
CRON_MORNING_TIME=0 9 * * *
CRON_EVENING_TIME=0 17 * * *
```

**每次执行的任务：**
1. 检查今天和明天的可订餐情况
2. 为所有启用的用户查找所有可用的"自助"菜品
3. 自动为每个可用的自助餐下单（避免重复点餐）
4. 记录详细的操作日志
5. 如果没有自助餐，则选择其他可用菜品

## 🔧 高级配置

### 修改定时时间

**推荐方式（通过 CRON_SCHEDULES 环境变量）：**

在 `.env` 文件中设置多个定时任务：
```bash
# 基础配置：每天两次检查
CRON_SCHEDULES=0 9 * * *;0 17 * * *

# 密集配置：适用于自助餐（推荐）
CRON_SCHEDULES=0 8 * * *;0 9 * * *;0 11 * * *;0 14 * * *;0 17 * * *;0 18 * * *

# 工作日专用配置
CRON_SCHEDULES=0 9 * * 1-5;0 17 * * 1-5

# 频繁检查配置（每30分钟）
CRON_SCHEDULES=*/30 9-18 * * 1-5
```

或在 `docker-compose.yml` 中设置：
```yaml
environment:
  - CRON_SCHEDULES=0 8 * * *;0 9 * * *;0 11 * * *;0 17 * * *
```

**向后兼容方式：**

```bash
# 单独设置早晚餐时间（如果未设置 CRON_SCHEDULES）
CRON_MORNING_TIME=0 8 * * *     # 上午8点
CRON_EVENING_TIME=30 17 * * *   # 下午5点30分
```

**传统方式（修改代码）：**

如果你需要更复杂的配置，可以直接编辑 `AutoMeican/settings.py` 文件：

```python
# 在 settings.py 文件中找到 CRONJOBS 配置部分
# 现在会自动从 CRON_SCHEDULES 环境变量生成多个任务
CRON_SCHEDULES = "0 9 * * *;0 17 * * *;0 11 * * *"
```

**Cron 表达式说明：**
- `0 9 * * *`：每天上午9点执行
- `0 17 * * *`：每天下午5点执行
- `*/30 9-17 * * 1-5`：工作日（周一到周五）9点到17点每30分钟执行一次
- `0 8,12,18 * * *`：每天8点、12点、18点执行

修改后需要重新启动容器：
```bash
docker-compose restart
```

### 修改点餐逻辑

点餐逻辑在 `meican/meican_service.py` 文件中，你可以根据需要自定义：

```python
def find_and_order_buffet(self, email=None, password=None):
    """
    自定义点餐逻辑
    """
    # 1. 优先选择自助餐
    if "自助" in dish_name:
        # 选择自助餐
        pass
    
    # 2. 其他自定义逻辑
    # 比如：优先选择特定价格范围的菜品
    # 比如：避免某些不喜欢的菜品
    # 比如：根据星期几选择不同类型的菜品
```

常见的自定义需求：

1. **价格筛选**：只选择特定价格范围内的菜品
2. **关键词过滤**：避免包含特定关键词的菜品（如"辣"、"海鲜"等）
3. **营养偏好**：优先选择健康、低脂、素食等类型的菜品
4. **时间策略**：根据不同时间段选择不同类型的菜品

### 自定义日志配置

可以在 `settings.py` 中修改 `LOGGING` 配置来自定义日志行为：

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/data/logs/meican_orders.log',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'meican': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 数据库配置

默认使用 SQLite 数据库，如果需要使用其他数据库（如 MySQL、PostgreSQL），可以修改 `DATABASES` 配置：

```python
# MySQL 配置示例
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'automeican',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 安全配置

生产环境建议进行以下安全配置：

1. **设置强密钥**：
   
   ```bash
   export DJANGO_SECRET_KEY="your-very-long-and-random-secret-key"
   ```
   
2. **关闭调试模式**：
   ```bash
   export DJANGO_DEBUG="False"
   ```

3. **配置允许的主机**：
   ```python
   ALLOWED_HOSTS = ['your-domain.com', 'localhost']
   ```

4. **启用 HTTPS**（如果有域名）：
   ```python
   SECURE_SSL_REDIRECT = True
   CSRF_COOKIE_SECURE = True
   SESSION_COOKIE_SECURE = True
   ```

## 📊 监控和故障排除

### 查看系统状态

```bash
# 查看容器运行状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 查看点餐日志
tail -f ~/.meican/logs/meican_orders.log

# 查看定时任务日志
tail -f ~/.meican/logs/meican_cron.log
```

### 常见问题解决

1. **登录失败**
   ```
   问题：用户登录美餐失败
   原因：密码错误或账户被锁定
   解决：检查 MEICAN_GLOBAL_PASSWORD 环境变量是否正确
   ```

2. **定时任务未执行**
   ```
   问题：自动点餐功能不工作
   原因：定时任务未正确启动
   解决：检查容器是否正常运行，查看 cron 日志
   ```

3. **点餐失败**
   ```
   问题：能登录但点餐失败
   原因：可能是美餐系统维护或菜单未开放
   解决：查看详细错误日志，稍后重试
   ```

4. **数据丢失**
   ```
   问题：重启后数据丢失
   原因：数据目录挂载错误
   解决：确保 ~/.meican 目录正确挂载
   ```

### 日志说明

**订餐日志** (`meican_orders.log`)：
```
2024-07-29 09:00:01 INFO 开始执行自动点餐任务
2024-07-29 09:00:02 INFO 找到 3 个活跃用户
2024-07-29 09:00:03 INFO 用户 user@example.com 在 2024-07-29 成功下单: 自助午餐
2024-07-29 09:00:04 ERROR 用户 user2@example.com 登录失败: 密码错误
```

**定时任务日志** (`meican_cron.log`)：
```
2024-07-29 09:00:00 开始执行定时任务
2024-07-29 09:00:05 定时任务执行完成
```

## 🔄 数据备份和恢复

### 备份数据

```bash
# 备份整个数据目录
tar -czf meican-backup-$(date +%Y%m%d).tar.gz ~/.meican/

# 仅备份数据库
cp ~/.meican/db.sqlite3 ~/db-backup-$(date +%Y%m%d).sqlite3
```

### 恢复数据

```bash
# 停止服务
docker-compose down

# 恢复数据
tar -xzf meican-backup-20240729.tar.gz -C ~/

# 重启服务
docker-compose up -d
```

## 🚀 部署到生产环境

### 使用 Docker Compose 部署

1. **准备生产配置**
   ```yaml
   # docker-compose.prod.yml
   services:
     app:
       build: .
       container_name: auto-meican-prod
       ports:
         - "8000:8000"
       environment:
         - MEICAN_GLOBAL_PASSWORD=${MEICAN_GLOBAL_PASSWORD}
         - DJANGO_DEBUG=False
         - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
       volumes:
         - ./data:/app/data
         - /etc/localtime:/etc/localtime:ro
       restart: always
   ```

2. **启动生产服务**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### 使用反向代理

配置 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 配置 HTTPS

使用 Let's Encrypt 配置 SSL：

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

## 🤝 参与贡献

我们欢迎所有形式的贡献！无论是报告 bug、提出新功能建议，还是提交代码，都是对项目的巨大帮助。

### 开发环境搭建

1. **Fork 项目**
   
   点击 GitHub 页面右上角的 Fork 按钮，将项目 fork 到你的账户

2. **克隆代码**
   ```bash
   git clone https://github.com/YOUR_USERNAME/AutoMeican.git
   cd AutoMeican
   ```

3. **设置开发环境**
   ```bash
   # 安装 Python 依赖
   pipenv install --dev
   pipenv shell
   
   # 设置环境变量
   export MEICAN_GLOBAL_PASSWORD="your_test_password"
   export DJANGO_DEBUG="True"
   
   # 初始化数据库
   python manage.py migrate
   
   # 启动开发服务器
   python manage.py runserver
   ```

4. **创建开发分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

### 开发指南

**代码风格**：
- 遵循 PEP 8 Python 代码规范
- 使用有意义的变量名和函数名
- 添加必要的注释和文档字符串
- 保持代码简洁和可读性

**提交规范**：
遵循 [约定式提交](https://www.conventionalcommits.org/zh-hans/) 规范：

```bash
# 新功能
git commit -m "feat: 添加邮件通知功能"

# 修复 bug
git commit -m "fix: 修复登录失败的问题"

# 文档更新
git commit -m "docs: 更新 README 安装说明"

# 代码重构
git commit -m "refactor: 优化点餐逻辑代码结构"

# 测试相关
git commit -m "test: 添加用户管理单元测试"
```

### 提交贡献

1. **确保代码质量**
   ```bash
   # 运行测试
   python manage.py test
   
   # 检查代码格式（如果配置了）
   black . --check
   flake8 .
   
   # 检查类型提示（如果使用）
   mypy .
   ```

2. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 你的功能描述"
   git push origin feature/your-feature-name
   ```

3. **创建 Pull Request**
   - 在 GitHub 上创建 Pull Request
   - 详细描述你的更改和解决的问题
   - 如果是 bug 修复，请描述重现步骤
   - 如果是新功能，请解释使用场景和好处

### 贡献类型

**🐛 Bug 报告**：
- 使用 [Bug 报告模板](.github/ISSUE_TEMPLATE/bug_report.md)
- 提供详细的重现步骤
- 包含系统环境信息
- 附上相关日志和截图

**💡 功能建议**：
- 使用 [功能请求模板](.github/ISSUE_TEMPLATE/feature_request.md)
- 详细描述期望的功能
- 解释使用场景和价值
- 提供设计思路（如果有）

**📚 文档改进**：
- 修复文档中的错误
- 添加缺失的说明
- 改进示例代码
- 翻译文档到其他语言

**🔧 代码贡献**：
- 修复已知 bug
- 实现新功能
- 性能优化
- 代码重构
- 添加测试用例

### 开发建议

1. **功能开发**：
   - 先创建 Issue 讨论设计方案
   - 保持功能的简洁性和易用性
   - 考虑向后兼容性
   - 添加相应的测试和文档

2. **Bug 修复**：
   - 理解问题的根本原因
   - 提供最小化的修复方案
   - 添加回归测试防止再次出现
   - 更新相关文档

3. **性能优化**：
   - 先进行性能分析找出瓶颈
   - 提供基准测试对比
   - 确保优化不影响功能正确性
   - 考虑内存使用和并发性能

### 社区行为准则

我们致力于营造一个开放、友好、多元化的社区环境：

- **尊重他人**：尊重不同的观点和经验
- **建设性交流**：提供有帮助的反馈和建议
- **协作精神**：乐于分享知识和经验
- **包容性**：欢迎所有背景的贡献者

### 获得帮助

如果在开发过程中遇到问题：

1. **查看文档**：首先查看 README 和 Wiki
2. **搜索 Issues**：看看是否有类似问题
3. **创建 Discussion**：在 GitHub Discussions 中寻求帮助
4. **联系维护者**：通过 Issue 或邮件联系项目维护者

## 项目路线图

我们计划在未来版本中添加以下功能：

### 🎯 近期计划 (v2.0)

- [ ] **Web 管理界面增强**
  - [ ] 订餐历史查看页面
- [ ] **智能点餐算法**
  - [ ] 基于用户偏好的菜品推荐
  - [ ] 营养均衡分析和建议
  - [ ] 避免重复菜品的智能策略
  - [ ] 价格预算控制功能
- [ ] **通知系统**
  - [ ] 微信/钉钉机器人通知
  - [ ] 订餐失败警报机制 - 邮件通知
  - [ ] 每日订餐统计报告

### 🌟 长期愿景 (v4.0+)

- [ ] **AI 驱动的智能助手**
  - [ ] 基于机器学习的个性化推荐
  - [ ] 智能日程安排集成
  - [ ] 健康建议和营养指导

## 🏆 贡献者名单

感谢所有为项目做出贡献的开发者！

### 核心维护者

- [@ZaneL1u](https://github.com/ZaneL1u) - 项目创始人和主要维护者

### 贡献者

<!-- 这里会自动更新贡献者列表 -->
*等待你的贡献！*

### 特别感谢

- 所有提交 Issue 和建议的用户
- 所有参与测试的早期用户
- 开源社区的支持和帮助

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

这意味着你可以：
- ✅ 商业使用
- ✅ 修改代码
- ✅ 分发代码
- ✅ 私人使用

但需要：
- 📋 保留版权声明
- 📋 保留许可证声明

### 第三方项目许可

本项目使用了以下开源项目，并遵循其相应的开源协议：

- **[LKI/meican](https://github.com/LKI/meican)** - MIT License
- **[Django](https://github.com/django/django)** - BSD License
- **[django-crontab](https://github.com/kraiz/django-crontab)** - MIT License  
- **[Requests](https://github.com/psf/requests)** - Apache License 2.0

详细的第三方许可信息请参考各项目的 LICENSE 文件。

## 🙏 致谢

### 开源项目

感谢以下开源项目为 AutoMeican 提供的支持：

- [Django](https://djangoproject.com/) - 强大的 Python Web 框架
- [django-crontab](https://github.com/kraiz/django-crontab) - Django 定时任务支持
- [Requests](https://requests.readthedocs.io/) - 优雅的 HTTP 库
- [Docker](https://docker.com/) - 容器化部署支持

### 特别致谢

**[LKI/meican](https://github.com/LKI/meican)** - 美餐 Python SDK 和命令行工具

本项目在开发过程中参考了 LKI 的美餐 SDK 项目，该项目采用 [MIT License](https://github.com/LKI/meican/blob/master/LICENSE) 开源协议。我们深深感谢 [@LKI](https://github.com/LKI) 和所有贡献者为美餐自动化工具生态系统做出的贡献。

- **项目地址**：https://github.com/LKI/meican
- **许可协议**：MIT License
- **主要贡献**：提供了美餐 API 接口的 Python 实现和最佳实践

根据 MIT 许可证的要求，我们在此声明：
- 保留原项目的版权声明
- 本项目基于自主开发，但在 API 接口设计上受到了该项目的启发
- 感谢开源社区的无私分享精神

### 社区支持

- 感谢所有在 GitHub 上给予 Star 和 Fork 的用户
- 感谢所有提交 Issue 和 Pull Request 的贡献者
- 感谢所有参与讨论和提供建议的社区成员

## 📞 联系方式

- **项目地址**：https://github.com/ZaneL1u/AutoMeican
- **问题反馈**：https://github.com/ZaneL1u/AutoMeican/issues
- **功能建议**：https://github.com/ZaneL1u/AutoMeican/discussions
- **邮箱联系**：hi@zaneliu.me

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ZaneL1u/AutoMeican&type=Date)](https://star-history.com/#ZaneL1u/AutoMeican&Date)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个 Star！⭐**

**🔔 Watch 项目获取最新更新通知**

**🍴 Fork 项目开始你的自定义之旅**

</div>

---

<div align="center">
  <sub>Built with ❤️ by <a href="https://github.com/ZaneL1u">ZaneL1u</a> and <a href="https://github.com/ZaneL1u/AutoMeican/graphs/contributors">contributors</a></sub>
</div>
