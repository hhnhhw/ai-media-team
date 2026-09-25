"""
文案AI微服务 — 运行在 Port 8001
接收主题/风格/字数 → 调用大模型 → 返回文章
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 修复 Windows GBK 终端 emoji 输出问题
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn
from openai import OpenAI
from config import (
    LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_MOCK,
    LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_DISPLAY_NAME, COPYWRITER_PORT,
)
from llm_utils import chat_text

app = FastAPI(title="文案AI服务", description="专职写文章、推文、种草笔记")


class WriteRequest(BaseModel):
    topic: str = Field(..., description="文章主题")
    style: str = Field(default="轻松幽默、吸引眼球", description="写作风格")
    word_count: int = Field(default=800, description="目标字数")
    platform: str = Field(default="公众号", description="发布平台（公众号/小红书/抖音等）")


class WriteResponse(BaseModel):
    success: bool
    title: str = ""
    content: str = ""
    word_count: int = 0
    platform: str = ""


MOCK_ARTICLES = {
    "default": {
        "title": "被南方人问爆了！哈尔滨冰雪大世界到底值不值得冲？",
        "content": """作为一个刚在哈尔滨冻掉脚趾头的过来人，我必须说：值！太值了！❄️

## 一、冰雪大世界到底有多震撼？

想象一下，你走进一个完全由冰块建成的城市——城堡、滑梯、宫殿，在夜晚灯光的映照下，整个园区就像《冰雪奇缘》里的艾伦戴尔照进现实。

主塔"冰雪之冠"足足有43米高，相当于15层楼！站在下面仰头看的那一刻，你会觉得人类的创造力真的太牛了。

## 二、南方小土豆生存指南

1. **穿什么？** 秋衣+保暖内衣+毛衣+羽绒服，下半身至少三层。暖宝宝贴满全身，尤其是脚底！
2. **手机怎么办？** 苹果用户注意了——你的手机会在-25°C的环境里疯狂掉电。带个充电宝，贴在暖宝宝上。
3. **拍照攻略** 下午4点半入园最好，能看到日落+开灯两种效果。冰灯亮起的瞬间，真的会WOW出声！

## 三、值不值那个票价？

说实话，300多的票价不便宜。但如果你把它当做一个"一生至少要去一次"的体验，那就值。那种站在冰雪城堡前、哈气成冰的幸福感，是照片永远传达不了的。

## 最后的碎碎念

哈尔滨不止有冰雪大世界。中央大街的马迭尔冰棍（没错，-30°C吃冰棍才是正确打开方式）、索菲亚教堂的雪景、松花江上的冰上娱乐……这座城市有一种"北方的浪漫"，等你来发现。

**所以，还在犹豫的南方小土豆们，买票吧！哈尔滨在等你！** 🧊✨""",
    },
}


def generate_mock_article(topic: str, style: str, word_count: int, platform: str) -> dict:
    """Mock 模式：根据主题生成一篇演示文章"""
    # 尝试匹配关键词
    article = MOCK_ARTICLES.get("default")
    if "哈尔滨" in topic or "冰雪" in topic:
        pass  # 用 default 那篇
    elif "北京" in topic and ("美食" in topic or "吃" in topic):
        article = {
            "title": f"北京美食地图｜{topic[:20]}",
            "content": f"""# {topic}

作为一个在北京吃了十年的资深吃货，今天掏心窝子分享几家真正值得去的店！🍜

## 一、涮肉篇

**聚宝源**——牛街上的传奇。手切鲜羊肉，入锅变色就捞，蘸上麻酱料，那一口下去，你会理解为什么北京人冬天离不开铜锅。

## 二、烤鸭篇

别再去全聚德排队了！**四季民福**的烤鸭性价比最高，皮酥肉嫩，配上甜面酱和葱丝，卷一张薄饼……绝了。

## 三、小吃篇

- **护国寺小吃**：豆汁儿（勇士请尝试）、焦圈、驴打滚、豌豆黄
- **姚记炒肝**：炒肝+包子，地道的北京早餐
- **方砖厂69号炸酱面**：老北京人的家常味

## 四、隐藏彩蛋

簋街的麻小、北新桥的卤煮、五道口的枣糕……北京的好吃的，三天三夜也说不完。

**收藏这篇，下次来北京跟着吃就对了！** 🦆🥢

---
*{platform} | {style} | 约{word_count}字*
""",
        }
    else:
        article = {
            "title": f"关于「{topic}」的一篇{platform}推文",
            "content": f"""# {topic}

![封面](https://picsum.photos/seed/{hash(topic) % 1000}/800/400)

> {style}风格 · {platform}特供

---

在这个快节奏的时代，我们总是在寻找那些能让人停下脚步的美好。

关于「{topic}」，我想说的是——这不仅是一个话题，更是一种生活态度。

## 为什么「{topic}」火了？

最近这个话题频频登上热搜，原因很简单：它击中了我们内心深处的某根弦。

## 深度解读

（此处应有{word_count}字的精彩内容，从多个角度解读{topic}的魅力所在。）

## 实用建议

1. 早做准备，提前规划
2. 找到志同道合的伙伴一起探索
3. 记录下每一个精彩瞬间
4. 分享给更多人，传递快乐

## 结语

生活不止眼前的苟且，还有{topic}带来的诗和远方。

**行动起来吧！让生活更有意思！** ✨

---
*本文由AI新媒体小编团队自动生成 · {platform} · {style} · 约{word_count}字*
""",
        }

    article["word_count"] = len(article["content"])
    article["platform"] = platform
    return article


def generate_with_llm(topic: str, style: str, word_count: int, platform: str) -> dict:
    """调用真实大模型生成文章"""
    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    system_prompt = f"""你是一个专业的{platform}文案写手。你的写作风格是：{style}。
要求：
- 写一篇关于「{topic}」的文章
- 字数约{word_count}字
- 使用Markdown格式，包含标题、小标题、emoji
- 语言生动有趣，有画面感
- 开头要抓人眼球，结尾要有行动号召
- 适合在{platform}上发布
"""
    # 字数×4 是经验估算；下限 1024 是为了给推理模型的 thinking 留出预算，
    # 否则短文章会因推理 token 吃光额度而拿到空正文。
    content = chat_text(
        client,
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请写一篇关于「{topic}」的文章，{word_count}字左右，风格：{style}"},
        ],
        temperature=LLM_TEMPERATURE,
        max_tokens=max(1024, min(word_count * 4, LLM_MAX_TOKENS)),
    )
    # 尝试提取标题
    lines = content.strip().split("\n")
    title = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped.lstrip("# ").strip()
            break
    if not title:
        title = topic

    return {
        "title": title,
        "content": content,
        "word_count": len(content),
        "platform": platform,
    }


@app.post("/generate", response_model=WriteResponse)
def generate(req: WriteRequest):
    if LLM_MOCK:
        result = generate_mock_article(req.topic, req.style, req.word_count, req.platform)
    else:
        result = generate_with_llm(req.topic, req.style, req.word_count, req.platform)

    return WriteResponse(success=True, **result)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": "mock" if LLM_MOCK else "live",
        "model": LLM_DISPLAY_NAME,
        "upstream_model": LLM_MODEL,
    }


if __name__ == "__main__":
    print(f"✍️  文案AI服务启动 → http://127.0.0.1:{COPYWRITER_PORT}")
    print(f"   模式: {'MOCK (演示)' if LLM_MOCK else f'LIVE ({LLM_DISPLAY_NAME})'}")
    uvicorn.run(app, host="0.0.0.0", port=COPYWRITER_PORT, log_level="info")
