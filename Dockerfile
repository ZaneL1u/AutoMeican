# 使用官方 Python 3.13 Alpine 镜像作为基础镜像
FROM python:3.13-alpine

# 设置工作目录
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN sed -i 's#https\?://dl-cdn.alpinelinux.org/alpine#https://mirrors.tuna.tsinghua.edu.cn/alpine#g' /etc/apk/repositories
RUN apk add --no-cache \
    dcron \
    curl \
    bash

COPY Pipfile Pipfile.lock ./
RUN pip install --no-cache-dir pipenv && \
    pipenv requirements > requirements.txt && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf ~/.cache/pip
COPY . .
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh
EXPOSE 8000
CMD ["/app/docker-entrypoint.sh"]
