# 📰 AI 新媒体小编团队

> **DeepSeek 主编调度 · AI 智能写作 · Pexels 多关键词配图**
>
> 一个由多个 AI Agent 协同工作的新媒体内容生产系统：**主编**理解需求并拆解任务，**文案AI**负责写作，**配图AI**负责配图，最终交付图文并茂的成稿。

---

## ✨ 核心特性

- 🧠 **主编智能体调度** — 基于 LangChain `create_agent`，自主分析需求、拆解任务、按序调用下属 Agent
- ✍️ **多平台风格适配** — 公众号 / 小红书 / 抖音 / 微博，支持幽默、文艺、专业、种草等多种文风
- 🎨 **智能实体提取配图** — 从正文逐句扫描可拍摄实体名词（地名 > 菜名 > 物品 > 品牌 > 景点），多关键词检索 Pexels 各取首位
- 💬 **对话历史持久化** — SQLite 存储会话与消息，跨 Streamlit 会话保留上下文
- 📡 **微服务架构** — 文案 / 配图各自独立 FastAPI 服务，可单独部署到云端
- 🔌 **Mock 演示模式** — 未配置 API Key 时自动降级为内置示例数据，零成本跑通全流程
- ☁️ **可发布为智能体** — 内置百度千帆应用广场配置文件（见 `agent-config/`）

---

## 🏗️ 系统架构

```
                    ┌──────────────────────────────┐
                    │   Streamlit 主编界面 :8501    │
                    │      main.py                 │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │   主编智能体 chief_editor.py  │
                    │  (LangChain create_agent)     │
                    │  · 需求分析  · 任务拆解       │
                    │  · 结果汇总  · 记忆管理       │
                    └───────┬──────────────┬────────┘
                            │              │
              write_article │              │ generate_illustration
                            ▼              ▼
              ┌──────────────────┐  ┌──────────────────┐
              │ 文案AI :8001      │  │ 配图AI :8002      │
              │ copywriter_service│  │ illustrator_service│
              │       .py         │  │        .py        │
              └────────┬─────────┘  └─────────┬─────────┘
                       │                      │
                       ▼                      ▼
              ┌──────────────────┐  ┌──────────────────┐
              │ DeepSeek / OpenAI │  │   Pexels API     │
              │  兼容 LLM 接口    │  │  多关键词图库检索 │
              └──────────────────┘  └──────────────────┘
                       │                      │
                       └──────────┬───────────┘
                                  ▼
                    ┌──────────────────────────────┐
                    │   SQLite 记忆库 memory.db     │
                    │  会话 / 消息 / 文章 / 配图记录 │
                    └──────────────────────────────┘
```

---

## 🚀 快速开始

### 前置要求

- Python **3.10+**
- [DeepSeek API Key](https://platform.deepseek.com/)（或任意 OpenAI 兼容接口）
- [Pexels API Key](https://www.pexels.com/api/)（免费申请）

### 1. 克隆并创建虚拟环境

```bash
git clone https://github.com/hhnhhw/ai-media-team.git
cd ai-media-team

python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

编辑 `.env`，填入你自己的密钥：

```ini
LLM_API_KEY=sk-your-api-key-here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-v4-pro
PEXELS_API_KEY=your-pexels-api-key-here
MOCK_MODE=false
```

> 💡 不填任何 Key 也能启动 —— 系统会自动进入 **Mock 演示模式**，用内置示例数据跑通全流程。

### 4. 一键启动

```bash
python run_services.py
```

该脚本会自动释放被占用的端口，然后依次拉起三个服务：

| 服务 | 地址 | 说明 |
|------|------|------|
| ✍️ 文案AI | http://127.0.0.1:8001 | 撰写文章、推文、种草笔记 |
| 🎨 配图AI | http://127.0.0.1:8002 | 关键词检索并返回配图 |
| 📰 主编界面 | http://127.0.0.1:8501 | Streamlit 交互主界面 |

浏览器打开 **http://127.0.0.1:8501** 即可使用，按 `Ctrl+C` 停止全部服务。

### 单独启动某个服务

```bash
python services/copywriter_service.py    # 仅文案AI
python services/illustrator_service.py   # 仅配图AI
streamlit run main.py                    # 仅主界面
```

---

## 📁 项目结构

```
ai-media-team/
├── main.py                       # Streamlit 主界面（聊天 UI、侧边栏、调度展示）
├── chief_editor.py               # 主编智能体：系统提示词 + LangChain Agent 装配
├── config.py                     # 全局配置与 .env 加载
├── memory.py                     # SQLite 记忆模块（会话/消息/文章/配图）
├── run_services.py               # 一键启动全部服务
├── test_fix.py                   # 配图检索效果测试脚本
├── requirements.txt
├── .env.example                  # 环境变量模板（复制为 .env 后填写）
│
├── services/                     # 独立微服务
│   ├── copywriter_service.py     # 文案AI  FastAPI :8001
│   └── illustrator_service.py    # 配图AI  FastAPI :8002
│
├── tools/                        # LangChain Tool 封装（主编调用入口）
│   ├── copywriter_tool.py        # write_article
│   └── illustrator_tool.py       # generate_illustration
│
└── agent-config/                 # 百度千帆应用广场发布配置包
    ├── qianfan-agent-import.json # 一键导入配置
    ├── agent-profile.json        # 智能体基本信息
    ├── system-prompt.md          # 完整系统提示词
    ├── tool-definitions.md       # 工具定义文档
    └── publish-guide.md          # 发布操作指南
```

---

## 🔌 API 接口

### 文案AI — `POST http://127.0.0.1:8001/generate`

```bash
curl -X POST http://127.0.0.1:8001/generate \
  -H "Content-Type: application/json" \
  -d '{
        "topic": "哈尔滨冰雪大世界旅游攻略",
        "style": "轻松幽默、吸引眼球",
        "word_count": 800,
        "platform": "公众号"
      }'
```

响应：

```json
{
  "success": true,
  "title": "被南方人问爆了！哈尔滨冰雪大世界到底值不值得冲？",
  "content": "……正文 Markdown……",
  "word_count": 812,
  "platform": "公众号"
}
```

### 配图AI — `POST http://127.0.0.1:8002/generate`

```bash
curl -X POST http://127.0.0.1:8002/generate \
  -H "Content-Type: application/json" \
  -d '{
        "prompt": "成都火锅, 麻辣红油锅底, 涮毛肚黄喉",
        "style": "真实摄影"
      }'
```

响应：

```json
{
  "success": true,
  "image_url": "https://images.pexels.com/photos/....jpeg",
  "image_urls": ["https://...", "https://..."],
  "prompt_used": "成都火锅, 麻辣红油锅底, 涮毛肚黄喉",
  "search_query": "成都火锅",
  "source": "pexels"
}
```

### 健康检查

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8002/health
```

---

## 🔄 主编工作流程

主编智能体严格按「四步法」调度：

1. **分析需求** — 理解主题类型，确定写作风格与目标平台（未指定则默认「轻松幽默」+「公众号」）
2. **调用文案AI** — 通过 `write_article` 工具生成完整文章
3. **提取配图实体** — 从**正文**逐句扫描可拍摄的实体名词，按视觉重要性排序取 3~8 个
   - ✅ 正确：`北京烤鸭, 全聚德烤鸭师傅切片, 枣红油亮鸭皮, 荷叶饼卷鸭肉`
   - ❌ 禁止：使用文章标题、抽象词（"美食""文化""体验"）、文章未提及的地点
4. **调用配图AI** — 以实体列表检索图片，汇总图文成稿

```
用户 → 主编 → ┌ 文案AI → 文章 ┐
              └ 配图AI → 图片 ┘ → 主编汇总 → 图文成稿
```

---

## ☁️ 部署为在线智能体

`agent-config/` 提供了发布到**百度千帆应用广场**的完整配置包：

1. 将两个微服务部署到公网（云函数 CFC / 云服务器 BCC / 容器服务 CCE 均可，详见 `agent-config/publish-guide.md`）
2. 修改 `qianfan-agent-import.json` 中的 `${COPYWRITER_SERVICE_URL}` 与 `${ILLUSTRATOR_SERVICE_URL}` 为实际地址
3. 在千帆控制台选择「导入配置」并上传该 JSON

详细步骤见 [`agent-config/README.md`](agent-config/README.md)。

---

## 🛠️ 技术栈

| 层次 | 技术 |
|------|------|
| 交互界面 | Streamlit |
| Agent 编排 | LangChain (`create_agent`) |
| 微服务 | FastAPI + Uvicorn |
| 大模型 | DeepSeek-V4-Pro（OpenAI 兼容接口） |
| 图库检索 | Pexels API |
| 持久化 | SQLite (WAL) |

---

## ❓ 常见问题

<details>
<summary><b>启动后界面显示「未连接」？</b></summary>

先确认两个后端服务已就绪，再刷新页面：

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8002/health
```
</details>

<details>
<summary><b>配图不准确怎么办？</b></summary>

通常是实体提取不够精准。优化 `chief_editor.py` 中 `CHIEF_EDITOR_PROMPT` 的提取规则，或直接用 `test_fix.py` 单独测试配图服务效果。
</details>

<details>
<summary><b>如何切换大模型？</b></summary>

修改 `.env` 中的 `LLM_BASE_URL` 与 `LLM_MODEL` 即可，任何 OpenAI 兼容接口都支持。
</details>

<details>
<summary><b>Windows 终端 emoji 报错 / 乱码？</b></summary>

各服务入口已内置 `sys.stdout.reconfigure(encoding="utf-8")` 处理。若仍异常，执行：

```powershell
chcp 65001
$env:PYTHONIOENCODING = "utf-8"
```
</details>

<details>
<summary><b>想清空历史对话数据？</b></summary>

删除根目录下的 `memory.db` 即可（该文件已在 `.gitignore` 中，不会被提交）。
</details>

---

## 🔐 安全说明

- ⚠️ **`.env` 已被 `.gitignore` 排除，切勿提交真实密钥**。仓库只提供 `.env.example` 模板。
- 若密钥曾不慎提交，请立即到对应平台**吊销并重新生成**。
- 对外部署微服务时，建议增加鉴权与限流，避免 API Key 被滥用。

---

## 📄 License

[MIT](LICENSE)

---

<p align="center">DeepSeek-V4 + Pexels + LangChain + Streamlit</p>
