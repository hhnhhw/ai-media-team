"""
配图AI微服务 — Port 8002
Pexels API 多关键词搜索 → 每词取首位 → 返回最匹配图片
"""
import sys, os, re, hashlib, requests
from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn
from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import (
    LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, IMAGE_MOCK, ILLUSTRATOR_PORT,
    PEXELS_API_KEY, LLM_TEMPERATURE, LLM_MAX_TOKENS_EXTRACT, LLM_DISPLAY_NAME,
)
from llm_utils import chat_text

app = FastAPI(title="配图AI服务")

class DrawRequest(BaseModel):
    prompt: str = Field(..., description="文章主题或实体列表")
    style: str = Field(default="真实摄影", description="图片风格偏好")

class DrawResponse(BaseModel):
    success: bool
    image_url: str = ""
    image_urls: list[str] = []
    prompt_used: str = ""
    search_query: str = ""
    source: str = ""

# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def _has_chinese(text: str) -> bool:
    return any('一' <= c <= '鿿' for c in text)

def _is_entity_list(text: str) -> bool:
    """输入是否已是逗号分隔的实体列表（跳过 LLM 重新提取）"""
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) < 2:
        return False
    short = sum(1 for p in parts if len(p) < 30)
    ch = sum(1 for p in parts if _has_chinese(p))
    avg = sum(len(p) for p in parts) / len(parts)
    return short / len(parts) > 0.6 and avg < 25 and ch / len(parts) > 0.3

# ═══════════════════════════════════════════════════════════════
# Unsplash 兜底图库
# ═══════════════════════════════════════════════════════════════

_FALLBACK = {
    "food": [
        "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1024",
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=1024",
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=1024",
    ],
    "city": [
        "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=1024",
        "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=1024",
        "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1024",
    ],
    "nature": [
        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1024",
        "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1024",
        "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1024",
    ],
    "tech": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1024",
        "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=1024",
        "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=1024",
    ],
    "people": [
        "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=1024",
        "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=1024",
        "https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?w=1024",
    ],
    "travel": [
        "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1024",
        "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=1024",
        "https://images.unsplash.com/photo-1528181304800-259b08848526?w=1024",
    ],
    "default": [
        "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1024",
    ],
}

_FALLBACK_KW = {
    "food":   ["美食","吃","餐厅","菜","饭","food","dish","烤鸭","火锅","小吃","甜点","咖啡","茶","面条","包子","饺子","烧烤","海鲜"],
    "city":   ["城市","建筑","街道","夜景","地标","city","building","street","上海","北京","广州","深圳","成都","重庆","杭州"],
    "nature": ["自然","风景","山","河","湖","海","森林","日落","nature","mountain","ocean","beach","花","雪","冰雪","冬天"],
    "tech":   ["科技","AI","智能","数码","手机","电脑","tech","digital","computer","芯片","机器人","软件"],
    "people": ["人物","人像","生活","people","portrait","团队","社区","人群","朋友","家庭"],
}

def _pick_fallback(prompt: str) -> str:
    best, best_score = "travel", 0
    for cat, kws in _FALLBACK_KW.items():
        s = sum(1 for kw in kws if kw in prompt.lower())
        if s > best_score:
            best_score, best = s, cat
    urls = _FALLBACK.get(best, _FALLBACK["default"])
    return urls[int(hashlib.md5(prompt.encode()).hexdigest(), 16) % len(urls)]

# ═══════════════════════════════════════════════════════════════
# Pexels API 搜索
# ═══════════════════════════════════════════════════════════════

def _search_pexels(query: str, count: int = 15) -> list[dict]:
    """搜索 Pexels，返回 [{url, alt, photographer, id}]"""
    if not PEXELS_API_KEY:
        return []
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": count, "orientation": "landscape", "size": "large"},
            headers={"Authorization": PEXELS_API_KEY},
            timeout=15,
        )
        resp.raise_for_status()
        photos = []
        for p in resp.json().get("photos", []):
            url = p.get("src", {}).get("large") or p.get("src", {}).get("original") or ""
            if url:
                photos.append({"url": url, "alt": (p.get("alt") or "").strip(),
                               "photographer": p.get("photographer", ""), "id": str(p.get("id", ""))})
        print(f"[配图AI] Pexels '{query[:30]}' → {len(photos)} 张")
        return photos
    except Exception as e:
        print(f"[配图AI] Pexels 失败: {e}")
        return []

# ═══════════════════════════════════════════════════════════════
# 关键词提取
# ═══════════════════════════════════════════════════════════════

def _extract_keywords(prompt: str) -> list[str]:
    """从 prompt 提取关键词：实体列表直接用，文章描述用LLM提取"""
    if _is_entity_list(prompt):
        entities = [e.strip() for e in prompt.split(",") if e.strip() and len(e.strip()) < 40]
        print(f"[配图AI] 实体: {entities[:5]}")
        return entities[:5]

    # 文章描述 → LLM 提取
    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    try:
        text = chat_text(
            client,
            model=LLM_MODEL,
            messages=[{"role": "user", "content":
                f"提取2-5个可拍摄的视觉关键词（地名/菜名/景点/物品）。只输出逗号分隔。\n{prompt[:300]}"}],
            temperature=LLM_TEMPERATURE, max_tokens=LLM_MAX_TOKENS_EXTRACT,
        )
        entities = [e.strip() for e in text.replace("、", ",").replace("，", ",").split(",") if e.strip()]
        if entities:
            print(f"[配图AI] LLM提取: {entities[:5]}")
            return entities[:5]
    except Exception:
        pass
    return [prompt[:40]]

# ═══════════════════════════════════════════════════════════════
# 主接口
# ═══════════════════════════════════════════════════════════════

@app.post("/generate", response_model=DrawResponse)
def generate(req: DrawRequest):
    if IMAGE_MOCK:
        url = _pick_fallback(req.prompt)
        return DrawResponse(success=True, image_url=url, image_urls=[url],
                          prompt_used=req.prompt, search_query="[Mock]", source="Unsplash (Mock)")

    prompt = req.prompt

    # 1. 提取关键词
    keywords = _extract_keywords(prompt)
    if not keywords:
        keywords = [prompt[:40]]
    print(f"[配图AI] 关键词({len(keywords)}): {keywords}")

    # 2. 每个关键词搜 Pexels，取各自排名第1的图片
    urls = []
    seen = set()
    for kw in keywords[:3]:
        photos = _search_pexels(kw, count=3)
        for p in photos:
            url = p.get("url", "")
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
                print(f"[配图AI] '{kw}' -> Pexels#{p.get('id','?')}")
                break  # 只取该关键词的第1名

    # 3. 兜底
    if not urls:
        url = _pick_fallback(prompt)
        return DrawResponse(success=True, image_url=url, image_urls=[url],
                          prompt_used=prompt, search_query=", ".join(keywords[:3]),
                          source="Unsplash 降级图库")

    print(f"[配图AI] 输出 {len(urls)} 张")
    return DrawResponse(success=True, image_url=urls[0], image_urls=urls[:3],
                      prompt_used=prompt, search_query=", ".join(keywords[:3]),
                      source=f"Pexels ({len(urls)} 张)")

@app.get("/health")
def health():
    return {"status": "ok", "mode": "mock" if IMAGE_MOCK else "live",
            "model": LLM_DISPLAY_NAME,
            "upstream_model": LLM_MODEL,
            "search": f"Pexels API + {LLM_DISPLAY_NAME} 智能筛选"}

if __name__ == "__main__":
    print(f"🎨 配图AI服务 → http://127.0.0.1:{ILLUSTRATOR_PORT}  |  "
          f"{'MOCK' if IMAGE_MOCK else f'Pexels + {LLM_DISPLAY_NAME}'}")
    uvicorn.run(app, host="0.0.0.0", port=ILLUSTRATOR_PORT, log_level="info")
