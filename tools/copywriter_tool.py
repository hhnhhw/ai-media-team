"""
文案AI 的 LangChain Tool 封装
通过网络请求调用文案微服务 (Port 8001)，实现跨域协同
"""
import requests
from langchain_core.tools import tool
from config import COPYWRITER_URL


@tool
def write_article(topic: str, style: str = "轻松幽默，吸引眼球", word_count: int = 800, platform: str = "公众号") -> str:
    """
    调用文案AI撰写文章。当你需要为一篇推文/笔记/公众号文章生成文案时使用此工具。

    Args:
        topic: 文章主题，例如"哈尔滨冰雪大世界旅游攻略"
        style: 写作风格，例如"幽默风趣""文艺清新""专业严谨""小红书种草风"
        word_count: 目标字数，默认800
        platform: 目标平台，例如"公众号""小红书""抖音""微博"

    Returns:
        包含标题和正文的完整文章（Markdown格式）
    """
    try:
        resp = requests.post(
            f"{COPYWRITER_URL}/generate",
            json={"topic": topic, "style": style, "word_count": word_count, "platform": platform},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            return f"【标题】{data['title']}\n\n【正文】\n{data['content']}\n\n（字数：{data['word_count']}）"
        return f"❌ 文案生成失败：{data}"
    except requests.ConnectionError:
        return f"❌ 无法连接到文案AI服务（{COPYWRITER_URL}），请确保服务已启动。"
    except Exception as e:
        return f"❌ 调用文案AI时出错：{str(e)}"
