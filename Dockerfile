# FanqieQimaoDownloader Docker镜像
# 基于 Python 3.10 slim 镜像

FROM python:3.10-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data/books /app/data/epubs /app/logs

# 初始化数据库
RUN python init_db.py

# 暴露端口
EXPOSE 4568

# 设置数据卷
VOLUME ["/app/data", "/app/logs"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:4568/health', timeout=5)" || exit 1

# 启动命令
CMD ["python", "start.py"]
