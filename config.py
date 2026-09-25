"""
AI新媒体小编团队 —— 全局配置
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ──────────────────────────────────────────────────────
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")

# ── 图片搜索 API ────────────────────────────────────────────
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# ── 服务端口 ─────────────────────────────────────────────────
COPYWRITER_PORT = int(os.getenv("COPYWRITER_PORT", "8001"))
ILLUSTRATOR_PORT = int(os.getenv("ILLUSTRATOR_PORT", "8002"))
COPYWRITER_URL = os.getenv("COPYWRITER_URL", f"http://127.0.0.1:{COPYWRITER_PORT}")
ILLUSTRATOR_URL = os.getenv("ILLUSTRATOR_URL", f"http://127.0.0.1:{ILLUSTRATOR_PORT}")

# ── Mock 模式 ────────────────────────────────────────────────
_global_mock = os.getenv("MOCK_MODE", "").lower()
LLM_MOCK = (not LLM_API_KEY) or _global_mock == "true"
IMAGE_MOCK = LLM_MOCK
