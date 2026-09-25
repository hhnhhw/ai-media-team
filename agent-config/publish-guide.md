# 千帆应用广场发布指南

本文档指导你如何将"AI新媒体小编团队"智能体发布到百度千帆应用广场。

---

## 📋 发布前准备

### 1. 准备工作

- ✅ 百度智能云账号（已实名认证）
- ✅ 千帆平台访问权限
- ✅ DeepSeek API Key（或其他大模型 API Key）
- ✅ Pexels API Key（用于配图搜索）
- ✅ 后端服务部署（文案AI和配图AI服务）

### 2. 部署后端服务

你需要部署两个微服务：

#### 方案 A: 百度云函数（推荐）

1. **部署文案AI服务**
   - 代码路径: `services/copywriter_service.py`
   - 端口: 8001
   - 环境变量: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`

2. **部署配图AI服务**
   - 代码路径: `services/illustrator_service.py`
   - 端口: 8002
   - 环境变量: `PEXELS_API_KEY`, `LLM_API_KEY`, `LLM_BASE_URL`

#### 方案 B: 云服务器部署

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动文案AI服务
python services/copywriter_service.py &

# 3. 启动配图AI服务
python services/illustrator_service.py &

# 4. 验证服务
curl http://localhost:8001/health
curl http://localhost:8002/health
```

---

## 🚀 千帆智能体配置步骤

### 步骤 1: 创建智能体

1. 登录 [千帆控制台](https://console.bce.baidu.com/qianfan/)
2. 进入 **应用广场** → **创建应用**
3. 选择 **智能体** 类型

### 步骤 2: 填写基本信息

参考 `agent-profile.json` 文件填写：

- **应用名称**: AI新媒体小编团队
- **应用描述**: 🤖 你的专属新媒体内容创作团队！主编智能体统筹调度，文案AI撰写吸睛文案，配图AI智能搜索高质量配图。
- **应用图标**: 📰（或上传自定义图标）
- **应用分类**: 内容创作
- **标签**: 新媒体、文案写作、配图、公众号、小红书、抖音、微博

### 步骤 3: 配置模型

- **模型选择**: DeepSeek-V4-Pro（或其他支持的模型）
- **Temperature**: 1.0
- **Max Tokens**: 4096
- **流式输出**: 开启

### 步骤 4: 配置系统提示词

将 `system-prompt.md` 的完整内容复制到千帆的 **系统提示词** 配置区域。

### 步骤 5: 配置工具（关键步骤）

#### 工具 1: write_article

```json
{
  "name": "write_article",
  "description": "撰写各种风格的文章、推文、种草笔记",
  "type": "function",
  "parameters": {
    "type": "object",
    "properties": {
      "topic": {
        "type": "string",
        "description": "文章主题"
      },
      "style": {
        "type": "string",
        "description": "写作风格",
        "default": "轻松幽默，吸引眼球"
      },
      "word_count": {
        "type": "integer",
        "description": "目标字数",
        "default": 800
      },
      "platform": {
        "type": "string",
        "description": "发布平台",
        "default": "公众号"
      }
    },
    "required": ["topic"]
  }
}
```

**API 配置:**
- 请求方式: POST
- URL: `{YOUR_SERVICE_URL}/copywriter/generate`
- 超时: 120秒

#### 工具 2: generate_illustration

```json
{
  "name": "generate_illustration",
  "description": "根据文章内容搜索高质量配图",
  "type": "function",
  "parameters": {
    "type": "object",
    "properties": {
      "prompt": {
        "type": "string",
        "description": "文章中的具体实体列表（逗号分隔）"
      },
      "style": {
        "type": "string",
        "description": "图片风格",
        "default": "真实摄影"
      }
    },
    "required": ["prompt"]
  }
}
```

**API 配置:**
- 请求方式: POST
- URL: `{YOUR_SERVICE_URL}/illustrator/generate`
- 超时: 180秒

### 步骤 6: 配置开场白

```
👋 你好！我是AI新媒体小编团队的主编「老编」。

我手下有两位得力干将：
- ✍️ 文案AI（小文）：撰写各种风格的文案
- 🎨 配图AI（小图）：智能搜索高质量配图

告诉我你想写什么主题，我们帮你一键生成完整推文！

示例：
- "帮我写一篇关于北京美食的公众号推文"
- "写一篇小红书种草笔记，推荐哈尔滨冰雪大世界"
- "生成一篇抖音风格的短视频脚本"
```

### 步骤 7: 配置示例对话

添加以下示例对话，帮助用户快速上手：

**示例 1:**
```
用户: 帮我写一篇关于北京烤鸭的公众号推文
助手: 收到！我来安排团队为你生成...
```

**示例 2:**
```
用户: 写一篇小红书笔记，推荐哈尔滨冰雪大世界
助手: 好的！小红书种草风走起...
```

---

## 🧪 测试与发布

### 测试检查清单

- [ ] 文案生成功能正常
- [ ] 配图搜索功能正常
- [ ] 多平台风格切换正常
- [ ] 流式输出正常
- [ ] 错误处理正常
- [ ] 响应时间在可接受范围内

### 发布流程

1. **内部测试**: 先在千帆控制台进行对话测试
2. **提交审核**: 点击"提交审核"按钮
3. **等待审核**: 通常 1-3 个工作日
4. **发布上线**: 审核通过后点击"发布"

---

## 📊 发布后运营

### 监控指标

- 日活用户数
- 平均对话轮次
- 工具调用成功率
- 用户满意度评分
- 错误率

### 优化建议

1. **根据用户反馈调整系统提示词**
2. **优化工具响应速度**
3. **增加更多写作风格选项**
4. **支持更多图片搜索源**

---

## 🔧 常见问题

### Q1: 工具调用失败怎么办？

检查：
- 后端服务是否正常运行
- API Key 是否配置正确
- 网络连接是否正常
- 超时时间是否足够

### Q2: 如何切换大模型？

在千帆控制台的模型配置中，可以选择不同的模型：
- DeepSeek-V4-Pro（推荐）
- ERNIE-Bot-4
- GPT-4
- 其他支持的模型

### Q3: 如何添加更多写作风格？

在 `system-prompt.md` 的风格识别规则中添加新风格，并在 `write_article` 工具的 `style` 参数枚举中添加选项。

### Q4: 如何支持更多平台？

在 `system-prompt.md` 的平台识别规则中添加新平台，并在 `write_article` 工具的 `platform` 参数枚举中添加选项。

---

## 📁 配置文件清单

发布所需的配置文件位于 `agent-config/` 目录：

```
agent-config/
├── agent-profile.json    # 智能体基本信息配置
├── system-prompt.md      # 系统提示词
├── tool-definitions.md   # 工具定义文档
└── publish-guide.md      # 本发布指南
```

---

## 💡 高级配置（可选）

### 1. 添加知识库

可以上传以下知识库增强能力：
- 新媒体运营指南
- 各平台内容规范
- 热门话题库
- 写作技巧库

### 2. 添加多模态能力

- 支持用户上传图片作为参考
- 支持生成图片（集成图像生成API）

### 3. 添加记忆功能

- 保存用户的历史创作
- 记住用户偏好的写作风格
- 个性化推荐

---

## 📞 技术支持

如有问题，请联系：
- 千帆平台文档: https://cloud.baidu.com/doc/WENXINWORKSHOP/index.html
- 百度智能云客服: 400-890-0088

---

**祝你发布成功！🎉**


[DuMate AI生成]