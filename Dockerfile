# ── AI 新媒体小编团队 — 单容器多进程镜像 ──────────────────────
# 三个进程（文案AI 8001 / 配图AI 8002 / Streamlit 8501）由 supervisor.py
# 统一拉起，只对外暴露 8501，作为一个 web_service 工作负载运行。
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# 依赖单独一层，代码变更时可复用缓存
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 仅复制运行所需内容（.env / .venv / memory.db 等由 .dockerignore 排除）
COPY config.py memory.py chief_editor.py main.py ./
COPY services/ ./services/
COPY tools/ ./tools/
COPY deploy/ ./deploy/

# 应用内默认以 127.0.0.1:8001 / 8002 访问两个内部服务，无需额外配置
ENV COPYWRITER_PORT=8001 \
    ILLUSTRATOR_PORT=8002

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health',timeout=4).status==200 else 1)"

CMD ["python", "deploy/supervisor.py"]
