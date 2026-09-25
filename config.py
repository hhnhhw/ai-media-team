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

# 对外展示用的模型名。留空则与 LLM_MODEL 相同。
# 用途：实际调用的 model 名可能是网关别名（如 deepseek-flash），
# 但界面/状态里想展示更友好的名称（如 deepseek-v4.1-flash）。
LLM_DISPLAY_NAME = os.getenv("LLM_DISPLAY_NAME", "").strip() or LLM_MODEL


def _env_float(name: str, default: float) -> float:
    """容错读取浮点环境变量：填错时回退默认值，而不是让整个进程起不来。"""
    try:
        return float(os.getenv(name, "") or default)
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "") or default)
    except (TypeError, ValueError):
        return default


# 采样温度。必须按所用模型调整：部分推理模型只接受 temperature=1.0，
# 传其他值会被服务端拒绝。
LLM_TEMPERATURE = _env_float("LLM_TEMPERATURE", 0.7)

# 输出长度上限（token）。
# ⚠️ 推理模型（如 deepseek 系列）会先输出 reasoning token，且这些 token
#    同样计入 max_tokens。预算偏小时会出现"思考写完了、正文还没开始"，
#    即 content 为空、finish_reason=length。因此这里要留足余量。
LLM_MAX_TOKENS = _env_int("LLM_MAX_TOKENS", 4096)
# 配图实体抽取的输出上限。任务本身只需几个关键词，但同样要给推理留余量，
# 上限只是"天花板"而非实际消耗，调大不会增加费用。
LLM_MAX_TOKENS_EXTRACT = _env_int("LLM_MAX_TOKENS_EXTRACT", 1024)

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
