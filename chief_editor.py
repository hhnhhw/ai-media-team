"""
主编智能体（总指挥AI）
基于 LangChain create_agent，调度文案AI和配图AI协同工作
兼容 langchain >= 1.3
"""
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from typing import Any, Callable

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_MOCK
from tools.copywriter_tool import write_article
from tools.illustrator_tool import generate_illustration

# ── 主编系统提示词 ────────────────────────────────────────────
CHIEF_EDITOR_PROMPT = """你是一个自媒体团队的**主编"老编"**。你的团队有两位AI成员：

1. **✍️ 文案AI（小文）**：负责撰写各种风格的文章、推文、种草笔记
2. **🎨 配图AI（小图）**：负责根据文章内容生成精美的配图

## 你的工作流程

当用户给你一个主题或需求时，请严格按以下步骤执行：

### 第一步：分析需求
- 理解用户想要什么类型的文章
- 确定写作风格（如果没有指定，默认"轻松幽默、吸引眼球"）
- 确定目标平台（如果没有指定，默认"公众号"）

### 第二步：调用文案AI
使用 `write_article` 工具，传入合适的参数：
- topic: 文章主题
- style: 写作风格
- word_count: 字数（默认800）
- platform: 发布平台

### 第三步：调用配图AI（最关键步骤）
从**文章正文**中逐句扫描，提取所有具体的、可拍摄的实体名词，用逗号拼接成 prompt。
- prompt 格式：**纯逗号分隔的实体名词，不要完整句子，不要标题**。
- 提取规则：地名>菜名>具体物品>品牌>景点，按视觉重要性排序
- 数量：至少 3 个，最多 8 个
- 示例：如果文章写"师傅手起刀落，108片枣红油亮的鸭肉整整齐齐码好"，提取"北京烤鸭, 全聚德烤鸭师傅切片, 枣红油亮鸭皮, 荷叶饼卷鸭肉"
- **严禁**：使用文章标题作为 prompt、使用抽象词（如"美食""文化""体验"）、添加文章未提及的地点
- style: 固定 **"真实摄影"**

### 第四步：整合呈现
将文案和配图整合成一篇完整的推文预览，包括：
- 📌 文章标题
- 🖼️ 配图（Markdown图片链接，必须包含配图AI返回的全部图片URL）
- 📝 正文内容

## 注意事项
- 必须先写文章再配图
- 配图 prompt 从**文章正文（非标题）** 中逐句提取具体的视觉实体
- 最终输出中必须包含配图AI返回的图片Markdown链接（![](url)格式）
"""

# ── 中间件：捕获 Agent 每一步操作 ──────────────────────────────
class StepCaptureMiddleware(AgentMiddleware):
    """捕获 Agent 的 tool 调用，用于前端展示调度过程"""

    def __init__(self):
        super().__init__()
        self.steps: list[dict] = []
        self._called_tools: set = set()

    def wrap_tool_call(self, request: Any, handler: Callable) -> Any:
        tool_name = request.tool if hasattr(request, "tool") else "unknown"
        tool_str = str(tool_name)

        if "write_article" in tool_str:
            if tool_str not in self._called_tools:
                self.steps.append({"agent": "主编", "msg": "正在分析需求... 先让文案AI写文章！"})
            self.steps.append({"agent": "文案AI", "msg": "收到！正在撰写文章..."})
        elif "generate_illustration" in tool_str:
            if tool_str not in self._called_tools:
                self.steps.append({"agent": "主编", "msg": "文章写好了！让配图AI搜索配图..."})
            self.steps.append({"agent": "配图AI", "msg": "收到！正在提取关键实体，Pexels 搜索图片..."})

        self._called_tools.add(tool_str)
        result = handler(request)
        self.steps.append({"agent": "主编", "msg": "该步骤完成！继续下一步..."})
        return result


def create_chief_editor(checkpointer=None):
    """创建主编 Agent，返回 (agent, tools, middleware)

    Args:
        checkpointer: LangGraph checkpointer（可选，用于持久化 Agent 记忆）
    """
    tools = [write_article, generate_illustration]

    if LLM_MOCK:
        return None, tools

    llm = ChatOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        model=LLM_MODEL,
        temperature=1.0,
        streaming=True,
    )

    middleware = StepCaptureMiddleware()

    agent_kwargs = dict(
        model=llm,
        tools=tools,
        system_prompt=CHIEF_EDITOR_PROMPT,
        middleware=[middleware],
    )
    if checkpointer is not None:
        agent_kwargs["checkpointer"] = checkpointer

    agent = create_agent(**agent_kwargs)

    return agent, tools, middleware
