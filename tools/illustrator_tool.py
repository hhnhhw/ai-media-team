"""
配图AI 的 LangChain Tool 封装
通过网络请求调用配图微服务 (Port 8002)，实现跨域协同
"""
import requests
from langchain_core.tools import tool
from config import ILLUSTRATOR_URL


@tool
def generate_illustration(prompt: str, style: str = "真实摄影") -> str:
    """
    搜索互联网上的真实照片/图片作为文章配图。当你需要为文章配图时使用此工具。

    IMPORTANT: prompt 必须列出文章中具体出现的实体（地名、菜名、景点、物品），用逗号分隔。
    例如文章提到哈尔滨冰雪大世界，prompt 写"哈尔滨冰雪大世界, 冰雪城堡夜景, 冰雕灯光秀"
    例如文章提到北京烤鸭，prompt 写"北京烤鸭, 全聚德, 烤鸭师傅切片, 油亮酥皮特写"
    不要写抽象概念或完整句子，只列具体可拍摄的实体名词。

    Args:
        prompt: 文章中的具体实体列表（逗号分隔的中文实体名词），越具体搜索结果越精准
        style: 图片风格，默认"真实摄影"搜索真实照片

    Returns:
        来自搜索引擎的真实图片URL
    """
    try:
        resp = requests.post(
            f"{ILLUSTRATOR_URL}/generate",
            json={"prompt": prompt, "style": style},
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            urls = data.get("image_urls", [data["image_url"]])
            url_list = "\n".join(f"- {u}" for u in urls[:3])
            return (
                f"✅ 配图搜索成功！（来源：{data.get('source', 'Bing')}，搜索词：{data.get('search_query', prompt)}）\n"
                f"主图：{data['image_url']}\n"
                f"备选图片：\n{url_list}"
            )
        return f"❌ 配图搜索失败：{data}"
    except requests.ConnectionError:
        return f"❌ 无法连接到配图AI服务（{ILLUSTRATOR_URL}），请确保服务已启动。"
    except Exception as e:
        return f"❌ 调用配图AI时出错：{str(e)}"
