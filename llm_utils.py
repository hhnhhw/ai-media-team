"""
大模型调用工具
==============
不同厂商的 OpenAI 兼容实现在两个细节上并不一致，这里统一收口，
避免每个调用点各写一份、各踩一次坑：

1. **推理模型把思考与正文分开放**（如 deepseek 系列）：
   思考过程在 `reasoning_content`，正文在 `content`，是两个独立字段。

2. **推理 token 同样计入 `max_tokens`**。预算偏小时会出现
   "思考写完了、正文还没开始"，表现为 `content` 为空且
   `finish_reason == "length"`。

因此**不能**简单地在 `content` 为空时回退到 `reasoning_content`：
那样会把模型没写完的思考过程当成文章正文返回，产出看起来像
"我们需要回答用户中文请求……"这样的废话。正确做法是给足预算，
并在真的被截断时用更大的预算重试一次。
"""
from typing import Any

# 重试时的绝对上限：避免调用方传入极大预算时把重试放大到不合理的值。
_RETRY_CEILING = 8192


def _pick_text(message: Any, finish_reason: str) -> str:
    """从回复消息里取正文文本。"""
    content = (getattr(message, "content", "") or "").strip()
    if content:
        return content
    if finish_reason == "length":
        # 被 max_tokens 截断：reasoning_content 只是没写完的思考，不能当正文
        return ""
    # 少数网关会把结果只放在 reasoning_content，此时才回退
    return (getattr(message, "reasoning_content", "") or "").strip()


def chat_text(client: Any, **kwargs: Any) -> str:
    """调用 chat.completions 并返回正文文本。

    若推理 token 吃光了 max_tokens 导致正文为空，会自动把预算翻倍重试一次
    （不超过 _RETRY_CEILING），避免调用方拿到空内容。
    """
    resp = client.chat.completions.create(**kwargs)
    choice = resp.choices[0]
    text = _pick_text(choice.message, choice.finish_reason)

    budget = kwargs.get("max_tokens")
    if not text and choice.finish_reason == "length" and budget:
        bigger = min(budget * 2, _RETRY_CEILING)
        if bigger > budget:
            retry_kwargs = dict(kwargs, max_tokens=bigger)
            resp = client.chat.completions.create(**retry_kwargs)
            choice = resp.choices[0]
            text = _pick_text(choice.message, choice.finish_reason)

    return text
