# ==================== 构建阶段（Builder Stage）====================
FROM python:3.11-slim AS builder

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装 Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# 复制依赖配置
COPY pyproject.toml ./

# 生成 lock 文件 + 安装依赖
RUN poetry lock --no-update
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-root

# 复制包结构代码（关键：复制 src/ 目录，因为包在 src/app）
COPY src/ ./src/
COPY README.md ./

# 构建项目 wheel 包（Poetry 会识别 src/app 为包）
RUN poetry build --format wheel

# ==================== 生产阶段（Production Stage）====================
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖和 wheel 包
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /app/dist/ ./dist/

# 安装项目
RUN pip install --no-cache-dir ./dist/*.whl

# 暴露端口
EXPOSE 8000

# 启动命令（适配包结构：app.main:app）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]