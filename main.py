"""
AI 新媒体小编团队 —— Streamlit 主界面
DeepSeek-V4 主编调度 · 文案AI写作 · Pexels 配图
"""
import streamlit as st
import time
import requests
import re
import uuid
from config import COPYWRITER_URL, ILLUSTRATOR_URL, LLM_MOCK
from memory import (
    init_db, create_conversation,
    list_conversations, delete_conversation,
    save_message, get_messages, save_article, save_image_record,
    get_agent_memory,
)

# ── 页面配置 ──────────────────────────────────────────────────
st.set_page_config(
    page_title="AI新媒体小编团队",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 自定义 CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .main-header h1 {
        color: white;
        font-size: 2rem;
        margin: 0;
    }
    .main-header p {
        color: rgba(255,255,255,0.85);
        margin: 0.3rem 0 0 0;
    }
    .agent-thinking {
        background: #f0f4ff;
        border-left: 4px solid #667eea;
        padding: 0.6rem 1rem;
        border-radius: 6px;
        margin: 0.4rem 0;
        animation: fadeIn 0.5s;
    }
    .agent-copywriter {
        background: #fff7ed;
        border-left: 4px solid #f97316;
        padding: 0.6rem 1rem;
        border-radius: 6px;
        margin: 0.4rem 0;
    }
    .agent-illustrator {
        background: #fdf2f8;
        border-left: 4px solid #ec4899;
        padding: 0.6rem 1rem;
        border-radius: 6px;
        margin: 0.4rem 0;
    }
    .final-result {
        background: #f0fdf4;
        border: 2px solid #22c55e;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-online { background: #dcfce7; color: #166534; }
    .status-offline { background: #fef2f2; color: #991b1b; }
</style>
""", unsafe_allow_html=True)

# ── 侧边栏 ────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 AI小编团队")

    st.divider()

    # 服务状态
    st.subheader("🔌 服务状态")
    col1, col2 = st.columns(2)
    try:
        r = requests.get(f"{COPYWRITER_URL}/health", timeout=2)
        col1.markdown(f'<span class="status-badge status-online">✍️ 文案AI</span>', unsafe_allow_html=True)
    except Exception:
        col1.markdown(f'<span class="status-badge status-offline">✍️ 未连接</span>', unsafe_allow_html=True)

    try:
        r = requests.get(f"{ILLUSTRATOR_URL}/health", timeout=2)
        col2.markdown(f'<span class="status-badge status-online">🎨 配图AI</span>', unsafe_allow_html=True)
    except Exception:
        col2.markdown(f'<span class="status-badge status-offline">🎨 未连接</span>', unsafe_allow_html=True)

    st.divider()

    # 模式提示
    if not LLM_MOCK:
        st.success("🚀 **Live 模式** — DeepSeek-V4 驱动\n\n✍️ 文案AI：智能写作\n🎨 配图AI：Pexels 多关键词搜索 · 各取首位")
    else:
        st.info("📌 **Mock 演示模式** — 配置 `.env` 中的 DeepSeek API Key 即可启用")

    st.divider()

    # ── 对话历史 ──────────────────────────────────────────────
    st.subheader("💬 对话历史")
    if st.button("＋ 新建对话", use_container_width=True):
        st.session_state.conv_id = None
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

    conversations = list_conversations()
    for conv in conversations:
        title = conv["title"] or f"对话 {conv['id']}"
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(title[:25], key=f"conv_{conv['id']}", use_container_width=True):
                st.session_state.conv_id = conv["id"]
                msgs = get_messages(conv["id"])
                st.session_state.messages = [
                    {"role": m["role"], "content": m["content"], "agent_name": m["agent_name"]}
                    for m in msgs
                ]
                st.rerun()
        with col2:
            if st.button("🗑", key=f"del_{conv['id']}"):
                delete_conversation(conv["id"])
                if st.session_state.conv_id == conv["id"]:
                    st.session_state.conv_id = None
                    st.session_state.messages = []
                st.rerun()

    st.divider()
    st.caption("DeepSeek-V4 + Pexels + LangChain + Streamlit")

# ── 主标题 ────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📰 AI 新媒体小编团队</h1>
    <p>DeepSeek-V4 主编调度 · AI 智能写作 · Pexels 多关键词配图</p>
</div>
""", unsafe_allow_html=True)

# ── 数据库初始化 ──────────────────────────────────────────────
init_db()
agent_memory = get_agent_memory()

# ── 会话状态初始化 ────────────────────────────────────────────
if "conv_id" not in st.session_state:
    st.session_state.conv_id = None  # 当前对话 ID

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())  # Agent 记忆的线程 ID

if "agent_memory" not in st.session_state:
    st.session_state.agent_memory = agent_memory  # LangGraph MemorySaver 实例

# ── 显示历史消息 ──────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── 检查服务是否在线 ──────────────────────────────────────────
def check_services():
    """检查文案和配图服务是否在线"""
    ok = True
    try:
        requests.get(f"{COPYWRITER_URL}/health", timeout=1)
    except Exception:
        ok = False
    try:
        requests.get(f"{ILLUSTRATOR_URL}/health", timeout=1)
    except Exception:
        ok = False
    return ok

# ── 主编调度逻辑（Mock 模式 / LangChain Agent 模式）────────────
def run_chief_editor_mock(user_input: str) -> dict:
    """
    Mock 模式：模拟主编的调度过程，不依赖真实 LLM
    通过分析用户输入中的关键词来决定文章风格和配图方向
    """
    steps = []
    progress_placeholder = st.empty()

    # Step 1: 主编分析需求
    with progress_placeholder.container():
        st.markdown('<div class="agent-thinking">🧠 <b>主编智能体</b>：收到！正在分析需求...</div>', unsafe_allow_html=True)
    steps.append({"agent": "主编", "msg": "收到！正在分析需求..."})
    time.sleep(0.3)

    # 提取关键词判断风格
    style = "轻松幽默，吸引眼球"
    platform = "公众号"
    if "小红书" in user_input:
        platform = "小红书"
        style = "小红书种草风，emoji丰富，亲切活泼"
    elif "抖音" in user_input:
        platform = "抖音"
        style = "短小精悍，节奏感强，爆点前置"
    elif "微博" in user_input:
        platform = "微博"
        style = "简洁有力，话题性强"

    if "幽默" in user_input or "搞笑" in user_input:
        style = "幽默风趣，段子手风格"
    elif "专业" in user_input or "深度" in user_input:
        style = "专业严谨，深度分析"
    elif "文艺" in user_input or "清新" in user_input:
        style = "文艺清新，温柔治愈"

    # Step 2: 调度文案AI
    with progress_placeholder.container():
        st.markdown(f'<div class="agent-thinking">🧠 <b>主编智能体</b>：任务拆解完成！@文案AI 你负责写一篇{style}的文章，目标平台{platform}。</div>', unsafe_allow_html=True)
        time.sleep(0.3)
        st.markdown(f'<div class="agent-copywriter">✍️ <b>文案AI（小文）</b>：收到！正在搜索最新资料，构思{platform}文案...</div>', unsafe_allow_html=True)
    steps.append({"agent": "主编", "msg": f"任务拆解完成！@文案AI 写一篇{style}的{platform}文章"})
    steps.append({"agent": "文案AI", "msg": f"收到！正在撰写{platform}文案..."})

    time.sleep(0.8)

    # 调用文案服务
    try:
        resp = requests.post(
            f"{COPYWRITER_URL}/generate",
            json={"topic": user_input, "style": style, "word_count": 800, "platform": platform},
            timeout=60,
        )
        article_data = resp.json() if resp.status_code == 200 else {}
    except Exception:
        article_data = {}

    title = article_data.get("title", f"关于「{user_input[:20]}」的{platform}推文")
    content = article_data.get("content", f"（文案生成中...请确保文案AI服务已启动）")
    word_count = article_data.get("word_count", len(content))

    with progress_placeholder.container():
        st.markdown('<div class="agent-copywriter">✍️ <b>文案AI（小文）</b>：写作完成！已生成一篇生动有趣的文案 ✅</div>', unsafe_allow_html=True)
    steps.append({"agent": "文案AI", "msg": f"文案生成完毕！标题：《{title}》，共{word_count}字"})

    time.sleep(0.3)

    # Step 3: 调度配图AI — 从用户输入和文章标题中提取具体实体
    def _extract_entities(text: str) -> list[str]:
        """从中文文本中提取具体的、可拍摄的名词短语"""
        words = re.findall(r'[一-鿿]{2,}|[a-zA-Z]{3,}', text)
        stopwords = {
            '关于', '一篇', '什么', '怎么', '如何', '这个', '那个',
            '这里', '那里', '帮助', '可以', '需要', '没有', '还是',
            '就是', '不是', '但是', '而且', '因为', '所以', '如果',
            '虽然', '然而', '之后', '之前', '以后', '已经', '只有',
            '我们', '他们', '你们', '自己', '大家', '每个', '很多',
            '一个', '这样', '那样', '其他', '所有', '这种', '那些',
            '这些', '文章', '内容', '风格', '平台', '主题', '一篇',
            '生成', '频率', '配图', '标题', '推文', '笔记', '帮我',
            '写一篇', '公众号', '小红书', '微博', '抖音', '轻松',
            '幽默', '专业', '深度', '文艺', '清新', '搞笑',
        }
        filtered = [w for w in words if w not in stopwords]
        seen = set()
        result = []
        for w in filtered:
            if w not in seen:
                seen.add(w)
                result.append(w)
        return result[:6]

    entities = _extract_entities(user_input + " " + title)
    if entities:
        image_prompt = ", ".join(entities)
    else:
        image_prompt = title[:40]
    with progress_placeholder.container():
        st.markdown(f'<div class="agent-thinking">🧠 <b>主编智能体</b>：文章很棒！现在 @配图AI 根据「{title[:30]}...」生成配图。</div>', unsafe_allow_html=True)
        time.sleep(0.3)
        st.markdown(f'<div class="agent-illustrator">🎨 <b>配图AI（小图）</b>：收到！提取关键实体，Pexels 多关键词搜索...</div>', unsafe_allow_html=True)
    steps.append({"agent": "主编", "msg": f"@配图AI 根据「{title[:30]}...」搜索配图"})
    steps.append({"agent": "配图AI", "msg": "提取关键实体，多关键词搜索..."})

    time.sleep(1.0)

    # 调用配图服务
    try:
        resp = requests.post(
            f"{ILLUSTRATOR_URL}/generate",
            json={"prompt": image_prompt, "style": "真实摄影"},
            timeout=60,
        )
        image_data = resp.json() if resp.status_code == 200 else {}
    except Exception:
        image_data = {}

    image_url = image_data.get("image_url", "https://picsum.photos/seed/fallback/1024/1024")

    with progress_placeholder.container():
        st.markdown('<div class="agent-illustrator">🎨 <b>配图AI（小图）</b>：Pexels 多关键词搜索完成 ✅</div>', unsafe_allow_html=True)
    steps.append({"agent": "配图AI", "msg": "多关键词搜索完毕！"})

    time.sleep(0.3)

    # Step 4: 整合结果
    with progress_placeholder.container():
        st.markdown('<div class="agent-thinking">🧠 <b>主编智能体</b>：所有任务完成！正在整合成完整推文...</div>', unsafe_allow_html=True)
    steps.append({"agent": "主编", "msg": "所有任务完成！正在整合最终推文..."})

    time.sleep(0.3)
    progress_placeholder.empty()

    return {
        "title": title,
        "content": content,
        "image_url": image_url,
        "platform": platform,
        "style": style,
        "steps": steps,
    }


def run_chief_editor_langchain(user_input: str):
    """使用 LangChain Agent 调度，逐 token 流式输出"""
    from chief_editor import create_chief_editor, StepCaptureMiddleware

    checkpointer = st.session_state.get("agent_memory", agent_memory)
    result_tuple = create_chief_editor(checkpointer=checkpointer)
    if result_tuple[0] is None:
        return run_chief_editor_mock(user_input)

    agent, tools, middleware = result_tuple
    thread_id = st.session_state.get("thread_id", "default")

    # 进度条区 + 流式文本区
    progress_area = st.empty()
    stream_area = st.empty()

    # 收集完整输出（用于最终返回）
    full_output_parts: list[str] = []
    seen_steps = 0

    # ── token 级流式生成器 ───────────────────────────────────
    def token_generator():
        nonlocal seen_steps
        invoke_input = {"messages": [{"role": "user", "content": user_input}]}
        invoke_config = {"configurable": {"thread_id": thread_id}}

        for chunk in agent.stream(invoke_input, invoke_config, stream_mode="messages"):
            # stream_mode="messages" 返回 (message_chunk, metadata) 元组
            if not isinstance(chunk, tuple) or len(chunk) < 2:
                continue

            msg_chunk = chunk[0]
            metadata = chunk[1]
            node_name = metadata.get("langgraph_node", "")

            # ── AI 文本 token ────────────────────────────
            # 只流式输出 model 节点的 token，跳过 tools 节点的原始返回
            if node_name == "model" and hasattr(msg_chunk, "content") and msg_chunk.content:
                token = msg_chunk.content
                if isinstance(token, str) and token:
                    full_output_parts.append(token)
                    yield token

            # ── 工具调用 ──────────────────────────────────
            if hasattr(msg_chunk, "tool_calls") and msg_chunk.tool_calls:
                for tc in msg_chunk.tool_calls:
                    tool_name = tc.get("name", "unknown")
                    if "write_article" in tool_name:
                        progress_area.markdown(
                            '<div class="agent-copywriter">✍️ <b>文案AI</b>：正在撰写文章...</div>',
                            unsafe_allow_html=True)
                    elif "generate_illustration" in tool_name:
                        progress_area.markdown(
                            '<div class="agent-illustrator">🎨 <b>配图AI</b>：Pexels 多关键词搜索...</div>',
                            unsafe_allow_html=True)

            # ── 工具结果 ──────────────────────────────────
            if node_name == "tools" and hasattr(msg_chunk, "content"):
                content = str(msg_chunk.content)
                tool_name = getattr(msg_chunk, "name", "")
                if "write_article" in tool_name:
                    progress_area.markdown(
                        '<div class="agent-copywriter">✍️ <b>文案AI</b>：文章撰写完成 ✅</div>',
                        unsafe_allow_html=True)
                elif "generate_illustration" in tool_name:
                    progress_area.markdown(
                        '<div class="agent-illustrator">🎨 <b>配图AI</b>：图片搜索完成 ✅</div>',
                        unsafe_allow_html=True)

            # ── 中间件步骤 ──────────────────────────────
            current_steps = len(middleware.steps)
            if current_steps > seen_steps:
                for step in middleware.steps[seen_steps:current_steps]:
                    css_class = "agent-thinking"
                    emoji = "🧠"
                    name = "主编智能体"
                    if step["agent"] == "文案AI":
                        css_class = "agent-copywriter"
                        emoji = "✍️"
                        name = "文案AI"
                    elif step["agent"] == "配图AI":
                        css_class = "agent-illustrator"
                        emoji = "🎨"
                        name = "配图AI"
                    progress_area.markdown(
                        f'<div class="{css_class}">{emoji} <b>{name}</b>：{step["msg"]}</div>',
                        unsafe_allow_html=True)
                seen_steps = current_steps

    # ── 流式渲染（带降级）─────────────────────────────────
    try:
        stream_area.write_stream(token_generator)
        output = "".join(full_output_parts)
    except Exception:
        # 流式失败 → 降级为同步调用
        invoke_input = {"messages": [{"role": "user", "content": user_input}]}
        invoke_config = {"configurable": {"thread_id": thread_id}}
        result_msg = agent.invoke(invoke_input, invoke_config)
        messages = result_msg.get("messages", [])
        output = str(messages[-1].content) if messages else ""

    progress_area.empty()

    return {
        "raw_output": output,
        "steps": middleware.steps,
    }


# ── 聊天输入 ──────────────────────────────────────────────────
if prompt := st.chat_input("输入你想写的主题，比如：帮我写一篇关于北京美食的推文..."):
    # ── 对话管理：没有对话则创建 ─────────────────────────────
    if st.session_state.conv_id is None:
        st.session_state.conv_id = create_conversation(prompt[:40])
    conv_id = st.session_state.conv_id

    # ── 添加并显示用户消息 ──────────────────────────────────
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message(conv_id, "user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    # 检查服务
    if not check_services():
        with st.chat_message("assistant"):
            st.error("⚠️ 文案AI或配图AI服务未启动！")
        st.stop()

    # ── 执行主编调度 + 展示结果 ──────────────────────────────
    with st.chat_message("assistant"):
        if LLM_MOCK:
            result = run_chief_editor_mock(prompt)
            st.markdown("---")
            st.markdown("## 📰 完整推文预览")
            st.markdown("---")

            if result.get("title"):
                st.markdown(f"## {result['title']}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"📱 平台：{result.get('platform', '公众号')}")
            with col2:
                st.caption(f"🎨 风格：{result.get('style', '默认')}")
            with col3:
                st.caption(f"📝 字数：{len(result.get('content', ''))}")

            image_url = result.get("image_url", "")
            mock_urls = [image_url] if image_url else []
            for i, u in enumerate(mock_urls):
                try:
                    img_bytes = requests.get(u, headers={"User-Agent": "Mozilla/5.0"}, timeout=15).content
                    st.image(img_bytes, caption=f"🎨 配图 {i+1}", use_container_width=True)
                except Exception:
                    st.caption(f"⚠️ 配图 {i+1} 加载失败")

            st.markdown(result.get("content", ""))

            # 保存到 SQLite
            save_article(conv_id, result.get("title", ""), result.get("content", ""),
                         result.get("platform", ""), result.get("style", ""))
            if result.get("image_url"):
                save_image_record(conv_id, result.get("search_query", ""),
                                  result["image_url"], "Mock")
            final_msg = f"## {result.get('title', '')}\n\n{result.get('content', '')}"
        else:
            result = run_chief_editor_langchain(prompt)
            raw = result.get("raw_output", "")
            # 提取并显示图片（文本已通过流式输出展示，这里只补图片）
            # 多种格式提取图片 URL
            all_img_urls = []
            # 1) Markdown 图片语法 ![](url)
            all_img_urls += re.findall(r'!\[.*?\]\((https?://[^\s\)]+)\)', raw)
            # 2) 直接图片链接
            all_img_urls += re.findall(r'https?://[^\s\n"\)]+\.(?:jpg|jpeg|png|webp)[^\s\n"\)]*', raw, re.IGNORECASE)
            # 3) 从工具返回文本中提取（主图/备选图片后的URL）
            for prefix in ['主图[：:]', '备选图片[：:]', '图片链接[：:]']:
                for m in re.finditer(prefix + r'\s*[-*]?\s*(https?://[^\s\n]+)', raw):
                    all_img_urls.append(m.group(1))
            # 4) 如果以上都没找到，提取所有 https:// 开头的URL中看起来像图片的
            if not all_img_urls:
                all_img_urls += [u for u in re.findall(r'https?://[^\s\n"\)]+', raw)
                                if any(u.lower().endswith(e) for e in ('.jpg','.jpeg','.png','.webp'))
                                or 'pexels.com' in u or 'unsplash.com' in u]
            # 去重保持顺序
            seen = set()
            all_img_urls = [u for u in all_img_urls if u not in seen and not seen.add(u)]
            img_loaded = 0
            for img_url in all_img_urls:
                try:
                    img_bytes = requests.get(img_url, headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }, timeout=15).content
                    st.image(img_bytes, caption=f"🎨 配图 {img_loaded+1}", use_container_width=True)
                    img_loaded += 1
                except Exception:
                    continue
            if img_loaded == 0 and all_img_urls:
                st.caption(f"⚠️ 图片加载失败（尝试了 {len(all_img_urls)} 个链接）")

            # 保存到 SQLite
            title_match = re.search(r'#+\s*(.+?)(?:\n|$)', raw)
            article_title = title_match.group(1).strip() if title_match else prompt[:40]
            save_article(conv_id, article_title, raw)
            for img_url in all_img_urls[:5]:
                save_image_record(conv_id, "", img_url, "Pexels")
            final_msg = raw

        # ── 保存消息 ──────────────────────────────────────────
        save_message(conv_id, "assistant", final_msg)
        st.session_state.messages.append({"role": "assistant", "content": final_msg})

        # 操作按钮
        st.divider()
        if LLM_MOCK:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.download_button(
                    "📥 下载文案 (Markdown)",
                    data=f"# {result.get('title', '推文')}\n\n![配图]({result.get('image_url', '')})\n\n{result.get('content', '')}",
                    file_name=f"{result.get('title', '推文')}.md",
                )
            with col2:
                if st.button("🔄 换一个风格"):
                    st.rerun()
            with col3:
                if st.button("🗑️ 清空对话"):
                    st.session_state.conv_id = None
                    st.session_state.messages = []
                    st.session_state.thread_id = str(uuid.uuid4())
                    st.rerun()
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📥 下载文案 (Markdown)",
                    data=result.get("raw_output", ""),
                    file_name="推文.md",
                )
            with col2:
                if st.button("🗑️ 清空对话"):
                    st.session_state.conv_id = None
                    st.session_state.messages = []
                    st.session_state.thread_id = str(uuid.uuid4())
                    st.rerun()


# ── 底部 ──────────────────────────────────────────────────────
st.divider()
st.caption("🤖 AI新媒体小编团队 | DeepSeek + Pexels + LangChain + Streamlit")
