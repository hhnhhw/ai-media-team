"""
配图AI微服务 — Port 8002
多源网络搜索（Pexels / Unsplash / Pixabay / 百度图片）→ 多模态视觉模型语义精选
流程：
  1. 从文章实体列表提取关键词（已是实体列表则直接使用，否则交给 LLM 抽取）
  2. 每个关键词并发搜索多个图源，合并去重得到候选池
  3. 若配置了视觉模型（VISION_MODEL），把候选图连同文章内容一起交给它，
     按「与正文的相关性」重新排序，挑出最贴合的前 N 张
  4. 全程降级：视觉模型失败 → 关键词顺序；无候选 → Unsplash 内置兜底图库
"""
import sys, os, re, hashlib, requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable
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
    LLM_TEMPERATURE, LLM_MAX_TOKENS_EXTRACT, LLM_DISPLAY_NAME,
    PEXELS_API_KEY, UNSPLASH_API_KEY, PIXABAY_API_KEY,
    IMAGE_SOURCE_PEXELS, IMAGE_SOURCE_UNSPLASH, IMAGE_SOURCE_PIXABAY, IMAGE_SOURCE_BAIDU,
    VISION_MODEL, VISION_API_KEY, VISION_BASE_URL, VISION_ENABLED,
)
from llm_utils import chat_text

app = FastAPI(title="配图AI服务")

# 交给视觉模型做精选时，最多送入的候选图数量（视觉调用有图片上限且逐张计费）
MAX_VISION_IMAGES = 8
# 每个图源、每个关键词的搜索条数
PER_SOURCE_COUNT = 4
# 最终返回的图片数量
TOP_K = 3

class DrawRequest(BaseModel):
    prompt: str = Field(..., description="文章主题或实体列表")
    style: str = Field(default="真实摄影", description="图片风格偏好")
    context: str = Field(default="", description="文章正文节选，用于视觉模型判断相关性")

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

def _normalize_url(u: str) -> str:
    """补全协议相对地址（如 //xxx → https://xxx）"""
    if not u:
        return ""
    if u.startswith("//"):
        return "https:" + u
    return u

# ═══════════════════════════════════════════════════════════════
# Unsplash 兜底图库（没有任何图源可用 / 搜索为空时的最后防线）
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
# 多源图片搜索
# 每个函数签名统一：_search_xxx(query, count) -> list[dict]
# dict 结构：{"url", "alt", "photographer", "id"}
# ═══════════════════════════════════════════════════════════════

def _search_pexels(query: str, count: int = PER_SOURCE_COUNT) -> list[dict]:
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

def _search_unsplash(query: str, count: int = PER_SOURCE_COUNT) -> list[dict]:
    if not UNSPLASH_API_KEY:
        return []
    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": count, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {UNSPLASH_API_KEY}"},
            timeout=15,
        )
        resp.raise_for_status()
        photos = []
        for p in resp.json().get("results", []):
            url = p.get("urls", {}).get("regular") or p.get("urls", {}).get("full") or ""
            if url:
                photos.append({"url": url,
                               "alt": (p.get("alt_description") or p.get("description") or "").strip(),
                               "photographer": (p.get("user", {}) or {}).get("name", ""), "id": str(p.get("id", ""))})
        print(f"[配图AI] Unsplash '{query[:30]}' → {len(photos)} 张")
        return photos
    except Exception as e:
        print(f"[配图AI] Unsplash 失败: {e}")
        return []

def _search_pixabay(query: str, count: int = PER_SOURCE_COUNT) -> list[dict]:
    if not PIXABAY_API_KEY:
        return []
    try:
        resp = requests.get(
            "https://pixabay.com/api/",
            params={"key": PIXABAY_API_KEY, "q": query, "per_page": count,
                    "image_type": "photo", "orientation": "horizontal", "safesearch": "true"},
            timeout=15,
        )
        resp.raise_for_status()
        photos = []
        for p in resp.json().get("hits", []):
            url = p.get("webformatURL") or p.get("largeImageURL") or ""
            if url:
                photos.append({"url": url, "alt": (p.get("tags") or "").strip(),
                               "photographer": p.get("user", ""), "id": str(p.get("id", ""))})
        print(f"[配图AI] Pixabay '{query[:30]}' → {len(photos)} 张")
        return photos
    except Exception as e:
        print(f"[配图AI] Pixabay 失败: {e}")
        return []

def _search_baidu(query: str, count: int = PER_SOURCE_COUNT) -> list[dict]:
    """百度图片搜索（免 key）。抓取 image.baidu.com 的 JSON 接口，返回百度 CDN 缩略图 URL。

    说明：这是网页抓取，稳定性不如官方 API；失败会静默返回空列表，由其他图源兜底。
    """
    try:
        params = {
            "tn": "resultjson_com",
            "ipn": "rj",
            "word": query,
            "pn": 0,
            "rn": count,
            "ie": "utf-8",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://image.baidu.com/",
            "Accept": "application/json, text/plain, */*",
        }
        resp = requests.get("https://image.baidu.com/search/acjson", params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        photos = []
        for item in resp.json().get("data", []):
            if not isinstance(item, dict):
                continue
            url = _normalize_url(item.get("middleURL") or item.get("thumbURL") or "")
            if not url:
                continue
            alt = item.get("fromPageTitleEnc") or item.get("fromPageTitle") or ""
            photos.append({"url": url, "alt": str(alt).strip(), "photographer": "", "id": str(item.get("id", ""))})
        print(f"[配图AI] 百度图片 '{query[:30]}' → {len(photos)} 张")
        return photos
    except Exception as e:
        print(f"[配图AI] 百度图片失败: {e}")
        return []

def _enabled_sources() -> list[tuple[str, Callable]]:
    """返回当前启用的图源列表 [(名称, 搜索函数)]，按优先级排序。"""
    sources = []
    if IMAGE_SOURCE_PEXELS and PEXELS_API_KEY:
        sources.append(("Pexels", _search_pexels))
    if IMAGE_SOURCE_UNSPLASH and UNSPLASH_API_KEY:
        sources.append(("Unsplash", _search_unsplash))
    if IMAGE_SOURCE_PIXABAY and PIXABAY_API_KEY:
        sources.append(("Pixabay", _search_pixabay))
    if IMAGE_SOURCE_BAIDU:
        sources.append(("百度", _search_baidu))
    return sources

# ═══════════════════════════════════════════════════════════════
# 关键词提取
# ═══════════════════════════════════════════════════════════════

def _extract_keywords(prompt: str) -> list[str]:
    """从 prompt 提取关键词：实体列表直接用，文章描述用LLM提取"""
    if _is_entity_list(prompt):
        entities = [e.strip() for e in prompt.split(",") if e.strip() and len(e.strip()) < 40]
        print(f"[配图AI] 实体: {entities[:5]}")
        return entities[:5]

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
# 多模态视觉精选
# ═══════════════════════════════════════════════════════════════

def _select_with_vision(context: str, prompt: str, candidates: list[dict]) -> list[dict]:
    """用视觉模型对候选图打分，返回按相关性排序后的候选列表。

    把文章内容 + 至多 MAX_VISION_IMAGES 张候选图一起发给视觉模型，
    让它选出最贴合正文的 TOP_K 张。选中的排前面，其余按原顺序追加在后。
    """
    client = OpenAI(api_key=VISION_API_KEY, base_url=VISION_BASE_URL)
    cands = candidates[:MAX_VISION_IMAGES]
    tail = candidates[MAX_VISION_IMAGES:]

    instruction = (
        "你是文章配图审核员。请根据文章内容，从下面的候选图片中选出最相关的3张。\n"
        f"文章内容：{(context or prompt)[:800]}\n"
        "要求：只输出被选中图片的编号，用逗号分隔，例如：1,3,5。不要输出任何其他文字。"
    )
    content = [{"type": "text", "text": instruction}]
    for i, c in enumerate(cands, 1):
        content.append({"type": "image_url", "image_url": {"url": c["url"]}})
        content.append({"type": "text", "text": f"[图{i}]"})

    resp = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{"role": "user", "content": content}],
        max_tokens=200,
    )
    text = (resp.choices[0].message.content or "").strip()
    print(f"[配图AI] 视觉精选输出: {text[:80]}")

    ordered, chosen = [], set()
    for x in re.findall(r"\d+", text):
        n = int(x)
        if 1 <= n <= len(cands) and n not in chosen:
            chosen.add(n)
            ordered.append(cands[n - 1])
    # 未被选中的候选按原顺序补齐，保证总有结果
    for i, c in enumerate(cands, 1):
        if i not in chosen:
            ordered.append(c)
    return ordered + tail

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
    keywords = _extract_keywords(prompt) or [prompt[:40]]
    print(f"[配图AI] 关键词({len(keywords)}): {keywords}")

    # 2. 多源并发搜索，按关键词顺序合并去重
    sources = _enabled_sources()
    per_kw = {kw: [] for kw in keywords[:3]}
    if sources:
        tasks = [(kw, name, fn) for kw in keywords[:3] for name, fn in sources]
        with ThreadPoolExecutor(max_workers=min(12, len(tasks))) as ex:
            futs = {ex.submit(fn, kw, PER_SOURCE_COUNT): (kw, name) for kw, name, fn in tasks}
            for fut in as_completed(futs):
                kw, name = futs[fut]
                try:
                    for p in fut.result():
                        p["_source"] = name
                        per_kw[kw].append(p)
                except Exception as e:
                    print(f"[配图AI] 搜索异常 ({name}/{kw[:20]}): {e}")

    candidates, seen = [], set()
    for kw in keywords[:3]:
        for p in per_kw[kw]:
            u = p.get("url", "")
            if u and u not in seen:
                seen.add(u)
                candidates.append(p)
    print(f"[配图AI] 候选池 {len(candidates)} 张（来自 {len(sources)} 个图源）")

    # 3. 多模态语义精选（失败则保持关键词顺序）
    source_note = "关键词相关性排序"
    if VISION_ENABLED and candidates:
        try:
            candidates = _select_with_vision(req.context, prompt, candidates)
            source_note = "视觉模型语义精选"
        except Exception as e:
            print(f"[配图AI] 视觉精选失败，回退关键词顺序: {e}")

    # 4. 兜底
    if not candidates:
        url = _pick_fallback(prompt)
        return DrawResponse(success=True, image_url=url, image_urls=[url],
                          prompt_used=prompt, search_query=", ".join(keywords[:3]),
                          source="Unsplash 降级图库")

    urls = [c["url"] for c in candidates[:TOP_K]]
    src_names = list(dict.fromkeys(c.get("_source", "") for c in candidates if c.get("_source")))
    print(f"[配图AI] 输出 {len(urls)} 张")
    return DrawResponse(success=True, image_url=urls[0], image_urls=urls,
                      prompt_used=prompt, search_query=", ".join(keywords[:3]),
                      source=f"{'+'.join(src_names)} · {source_note}")

@app.get("/health")
def health():
    return {"status": "ok", "mode": "mock" if IMAGE_MOCK else "live",
            "model": LLM_DISPLAY_NAME,
            "upstream_model": LLM_MODEL,
            "vision_model": VISION_MODEL or "未启用",
            "search": f"多源图库 + 百度图片，{'视觉精选' if VISION_ENABLED else '关键词排序'}，降级 Unsplash"}

if __name__ == "__main__":
    mode = "MOCK" if IMAGE_MOCK else f"多源搜索{' + 视觉精选' if VISION_ENABLED else ''}"
    print(f"🎨 配图AI服务 → http://127.0.0.1:{ILLUSTRATOR_PORT}  |  {mode}")
    uvicorn.run(app, host="0.0.0.0", port=ILLUSTRATOR_PORT, log_level="info")
